# app.py
# FastAPI endpoints básicos

from datetime import datetime
from enum import Enum
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field, conint, constr
from sqlalchemy import (
    Column,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session

# -----------------------------
# Configuración de DB (SQLite)
# -----------------------------
DATABASE_URL = "sqlite:///./tienda.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# -----------------------------
# Modelos SQLAlchemy
# -----------------------------
class OrderStatus(str, Enum):
    pending = "pending"
    paid = "paid"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False)
    sku = Column(String(64), nullable=False, unique=True, index=True)
    precio = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    talla = Column(String(16), nullable=True)
    color = Column(String(32), nullable=True)
    creado_en = Column(DateTime, default=func.now(), nullable=False)


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    telefono = Column(String(32), nullable=True)
    creado_en = Column(DateTime, default=func.now(), nullable=False)

    ordenes = relationship("Orden", back_populates="cliente")


class Orden(Base):
    __tablename__ = "ordenes"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    estado = Column(SAEnum(OrderStatus), default=OrderStatus.pending, nullable=False)
    creado_en = Column(DateTime, default=func.now(), nullable=False)

    cliente = relationship("Cliente", back_populates="ordenes")
    items = relationship("OrdenItem", back_populates="orden", cascade="all, delete-orphan")


class OrdenItem(Base):
    __tablename__ = "orden_items"
    __table_args__ = (
        UniqueConstraint("orden_id", "producto_id", name="uq_orden_producto"),
    )

    id = Column(Integer, primary_key=True, index=True)
    orden_id = Column(Integer, ForeignKey("ordenes.id"), nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)  # snapshot del precio al crear la orden
    subtotal = Column(Float, nullable=False)

    orden = relationship("Orden", back_populates="items")
    producto = relationship("Producto")


# -----------------------------
# Esquemas Pydantic (I/O)
# -----------------------------
# Productos
class ProductoBase(BaseModel):
    nombre: constr(strip_whitespace=True, min_length=1, max_length=120)
    sku: constr(strip_whitespace=True, min_length=1, max_length=64)
    precio: float = Field(gt=0)
    stock: conint(ge=0) = 0
    talla: Optional[constr(max_length=16)] = None
    color: Optional[constr(max_length=32)] = None


class ProductoCreate(ProductoBase):
    pass


class ProductoUpdate(BaseModel):
    nombre: Optional[constr(strip_whitespace=True, min_length=1, max_length=120)] = None
    precio: Optional[float] = Field(default=None, gt=0)
    stock: Optional[conint(ge=0)] = None
    talla: Optional[constr(max_length=16)] = None
    color: Optional[constr(max_length=32)] = None


class ProductoOut(BaseModel):
    id: int
    nombre: str
    sku: str
    precio: float
    stock: int
    talla: Optional[str]
    color: Optional[str]
    creado_en: datetime

    class Config:
        from_attributes = True


# Clientes
class ClienteBase(BaseModel):
    nombre: constr(strip_whitespace=True, min_length=1, max_length=120)
    email: EmailStr
    telefono: Optional[constr(strip_whitespace=True, max_length=32)] = None


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    nombre: Optional[constr(strip_whitespace=True, min_length=1, max_length=120)] = None
    telefono: Optional[constr(strip_whitespace=True, max_length=32)] = None


class ClienteOut(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    telefono: Optional[str]
    creado_en: datetime

    class Config:
        from_attributes = True


# Órdenes
class OrdenItemIn(BaseModel):
    producto_id: int
    cantidad: conint(gt=0)


class OrdenCreate(BaseModel):
    cliente_id: int
    items: List[OrdenItemIn]


class OrdenItemOut(BaseModel):
    id: int
    producto_id: int
    cantidad: int
    precio_unitario: float
    subtotal: float

    class Config:
        from_attributes = True


class OrdenOut(BaseModel):
    id: int
    cliente_id: int
    estado: OrderStatus
    creado_en: datetime
    items: List[OrdenItemOut]
    total: float

    class Config:
        from_attributes = True


class OrdenUpdateEstado(BaseModel):
    estado: OrderStatus


# -----------------------------
# Dependencias
# -----------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------
# Inicializar DB
# -----------------------------
Base.metadata.create_all(bind=engine)

# -----------------------------
# App y CORS
# -----------------------------
app = FastAPI(title="Tienda de Ropa — API Básica", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Rutas: Productos
# -----------------------------
@app.post("/productos", response_model=ProductoOut, status_code=status.HTTP_201_CREATED)
def crear_producto(payload: ProductoCreate, db: Session = Depends(get_db)):
    # Verificar SKU único
    existe = db.query(Producto).filter_by(sku=payload.sku).first()
    if existe:
        raise HTTPException(status_code=400, detail="SKU ya existe")
    prod = Producto(**payload.model_dump())
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod


@app.get("/productos", response_model=List[ProductoOut])
def listar_productos(
    db: Session = Depends(get_db),
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
):
    query = db.query(Producto)
    if q:
        like = f"%{q}%"
        query = query.filter(Producto.nombre.ilike(like))
    productos = query.offset(skip).limit(min(limit, 100)).all()
    return productos


@app.get("/productos/{producto_id}", response_model=ProductoOut)
def obtener_producto(producto_id: int, db: Session = Depends(get_db)):
    prod = db.query(Producto).get(producto_id)
    if not prod:
        raise HTTPException(404, "Producto no encontrado")
    return prod


@app.put("/productos/{producto_id}", response_model=ProductoOut)
def actualizar_producto(producto_id: int, payload: ProductoUpdate, db: Session = Depends(get_db)):
    prod = db.query(Producto).get(producto_id)
    if not prod:
        raise HTTPException(404, "Producto no encontrado")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(prod, k, v)
    db.commit()
    db.refresh(prod)
    return prod


@app.delete("/productos/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_producto(producto_id: int, db: Session = Depends(get_db)):
    prod = db.query(Producto).get(producto_id)
    if not prod:
        raise HTTPException(404, "Producto no encontrado")
    db.delete(prod)
    db.commit()
    return None


# -----------------------------
# Rutas: Clientes
# -----------------------------
@app.post("/clientes", response_model=ClienteOut, status_code=status.HTTP_201_CREATED)
def crear_cliente(payload: ClienteCreate, db: Session = Depends(get_db)):
    existe = db.query(Cliente).filter_by(email=payload.email).first()
    if existe:
        raise HTTPException(400, detail="Email ya registrado")
    cli = Cliente(**payload.model_dump())
    db.add(cli)
    db.commit()
    db.refresh(cli)
    return cli


@app.get("/clientes", response_model=List[ClienteOut])
def listar_clientes(db: Session = Depends(get_db), skip: int = 0, limit: int = 50, q: Optional[str] = None):
    query = db.query(Cliente)
    if q:
        like = f"%{q}%"
        query = query.filter(Cliente.nombre.ilike(like))
    clientes = query.offset(skip).limit(min(limit, 100)).all()
    return clientes


@app.get("/clientes/{cliente_id}", response_model=ClienteOut)
def obtener_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cli = db.query(Cliente).get(cliente_id)
    if not cli:
        raise HTTPException(404, "Cliente no encontrado")
    return cli


@app.put("/clientes/{cliente_id}", response_model=ClienteOut)
def actualizar_cliente(cliente_id: int, payload: ClienteUpdate, db: Session = Depends(get_db)):
    cli = db.query(Cliente).get(cliente_id)
    if not cli:
        raise HTTPException(404, "Cliente no encontrado")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(cli, k, v)
    db.commit()
    db.refresh(cli)
    return cli


@app.delete("/clientes/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cli = db.query(Cliente).get(cliente_id)
    if not cli:
        raise HTTPException(404, "Cliente no encontrado")
    db.delete(cli)
    db.commit()
    return None


# -----------------------------
# Rutas: Órdenes
# -----------------------------
@app.post("/ordenes", response_model=OrdenOut, status_code=status.HTTP_201_CREATED)
def crear_orden(payload: OrdenCreate, db: Session = Depends(get_db)):
    # Validar cliente
    cliente = db.query(Cliente).get(payload.cliente_id)
    if not cliente:
        raise HTTPException(400, detail="Cliente no existe")

    # Validar productos y stock, y calcular totales
    items_out = []
    total = 0.0
    productos_cache: dict[int, Producto] = {}

    for item in payload.items:
        prod = db.query(Producto).get(item.producto_id)
        if not prod:
            raise HTTPException(400, detail=f"Producto {item.producto_id} no existe")
        if prod.stock < item.cantidad:
            raise HTTPException(400, detail=f"Stock insuficiente para SKU {prod.sku}")
        productos_cache[item.producto_id] = prod

    # Crear orden
    orden = Orden(cliente_id=payload.cliente_id)
    db.add(orden)
    db.flush()  # obtiene orden.id

    for item in payload.items:
        prod = productos_cache[item.producto_id]
        precio = float(prod.precio)
        subtotal = precio * item.cantidad
        total += subtotal
        # Descontar stock
        prod.stock -= item.cantidad
        # Crear item
        oi = OrdenItem(
            orden_id=orden.id,
            producto_id=prod.id,
            cantidad=item.cantidad,
            precio_unitario=precio,
            subtotal=subtotal,
        )
        db.add(oi)

    db.commit()
    db.refresh(orden)

    # Construir respuesta con total
    return _orden_to_out(orden, db)


@app.get("/ordenes", response_model=List[OrdenOut])
def listar_ordenes(db: Session = Depends(get_db), skip: int = 0, limit: int = 50, estado: Optional[OrderStatus] = None, cliente_id: Optional[int] = None):
    query = db.query(Orden)
    if estado:
        query = query.filter(Orden.estado == estado)
    if cliente_id:
        query = query.filter(Orden.cliente_id == cliente_id)
    ordenes = query.order_by(Orden.creado_en.desc()).offset(skip).limit(min(limit, 100)).all()
    return [_orden_to_out(o, db) for o in ordenes]


@app.get("/ordenes/{orden_id}", response_model=OrdenOut)
def obtener_orden(orden_id: int, db: Session = Depends(get_db)):
    orden = db.query(Orden).get(orden_id)
    if not orden:
        raise HTTPException(404, "Orden no encontrada")
    return _orden_to_out(orden, db)


@app.put("/ordenes/{orden_id}/estado", response_model=OrdenOut)
def actualizar_estado_orden(orden_id: int, payload: OrdenUpdateEstado, db: Session = Depends(get_db)):
    orden = db.query(Orden).get(orden_id)
    if not orden:
        raise HTTPException(404, "Orden no encontrada")
    orden.estado = payload.estado
    db.commit()
    db.refresh(orden)
    return _orden_to_out(orden, db)


@app.delete("/ordenes/{orden_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_orden(orden_id: int, db: Session = Depends(get_db)):
    orden = db.query(Orden).get(orden_id)
    if not orden:
        raise HTTPException(404, "Orden no encontrada")
    # Al eliminar la orden, NO restauramos stock (simplificado). Ajusta según tu negocio.
    db.delete(orden)
    db.commit()
    return None


# -----------------------------
# Helpers
# -----------------------------

def _orden_to_out(orden: Orden, db: Session) -> OrdenOut:
    # Asegurar carga de items
    db.refresh(orden)
    items = [
        OrdenItemOut.model_validate(i, from_attributes=True)  # type: ignore
        for i in orden.items
    ]
    total = sum(i.subtotal for i in orden.items)
    base = {
        "id": orden.id,
        "cliente_id": orden.cliente_id,
        "estado": orden.estado,
        "creado_en": orden.creado_en,
        "items": items,
        "total": total,
    }
    return OrdenOut(**base)


# -----------------------------
# Ejecución local:
#   uvicorn app:app --reload
# -----------------------------
