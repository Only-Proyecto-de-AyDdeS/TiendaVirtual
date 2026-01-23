import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Usa variable de entorno o fallback local
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://tienda_user:tienda_pass@localhost:5432/tienda_db",
)

# Pool básico para dev; ajusta para prod
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# =========================================
# FILE: app/models.py
# =========================================
from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column,
    DateTime,
    Enum as SAEnum,
    Integer,
    String,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import NUMERIC
from sqlalchemy.orm import relationship
from .database import Base


class OrderStatus(str, Enum):
    pending = "pending"
    paid = "paid"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False, index=True)
    sku = Column(String(64), nullable=False, unique=True, index=True)
    precio = Column(NUMERIC(10, 2), nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    talla = Column(String(16))
    color = Column(String(32))
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_productos_nombre_color", "nombre", "color"),
    )


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    telefono = Column(String(32))
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)

    ordenes = relationship("Orden", back_populates="cliente")


class Orden(Base):
    __tablename__ = "ordenes"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="RESTRICT"), nullable=False, index=True)
    estado = Column(SAEnum(OrderStatus, name="order_status"), nullable=False, default=OrderStatus.pending)
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)

    cliente = relationship("Cliente", back_populates="ordenes")
    items = relationship("OrdenItem", back_populates="orden", cascade="all, delete-orphan")


class OrdenItem(Base):
    __tablename__ = "orden_items"

    id = Column(Integer, primary_key=True, index=True)
    orden_id = Column(Integer, ForeignKey("ordenes.id", ondelete="CASCADE"), nullable=False, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="RESTRICT"), nullable=False, index=True)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(NUMERIC(10, 2), nullable=False)  # snapshot al crear
    subtotal = Column(NUMERIC(10, 2), nullable=False)

    orden = relationship("Orden", back_populates="items")
    producto = relationship("Producto")

    __table_args__ = (
        UniqueConstraint("orden_id", "producto_id", name="uq_orden_producto"),
    )


# =========================================
# FILE: app/schemas.py
# =========================================
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, constr, conint
from .models import OrderStatus

# Productos
class ProductoBase(BaseModel):
    nombre: constr(strip_whitespace=True, min_length=1, max_length=120)
    sku: constr(strip_whitespace=True, min_length=1, max_length=64)
    precio: Decimal = Field(gt=0)
    stock: conint(ge=0) = 0
    talla: Optional[constr(max_length=16)] = None
    color: Optional[constr(max_length=32)] = None


class ProductoCreate(ProductoBase):
    pass


class ProductoUpdate(BaseModel):
    nombre: Optional[constr(strip_whitespace=True, min_length=1, max_length=120)] = None
    precio: Optional[Decimal] = Field(default=None, gt=0)
    stock: Optional[conint(ge=0)] = None
    talla: Optional[constr(max_length=16)] = None
    color: Optional[constr(max_length=32)] = None


class ProductoOut(BaseModel):
    id: int
    nombre: str
    sku: str
    precio: Decimal
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
    precio_unitario: Decimal
    subtotal: Decimal

    class Config:
        from_attributes = True


class OrdenOut(BaseModel):
    id: int
    cliente_id: int
    estado: OrderStatus
    creado_en: datetime
    items: List[OrdenItemOut]
    total: Decimal

    class Config:
        from_attributes = True


class OrdenUpdateEstado(BaseModel):
    estado: OrderStatus


# =========================================
# FILE: app/deps.py
# =========================================
from typing import Generator
from .database import SessionLocal

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================================
# FILE: app/main.py
# =========================================
from decimal import Decimal
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import Base, engine
from .models import Producto, Cliente, Orden, OrdenItem, OrderStatus
from .schemas import (
    ProductoCreate, ProductoUpdate, ProductoOut,
    ClienteCreate, ClienteUpdate, ClienteOut,
    OrdenCreate, OrdenOut, OrdenItemOut, OrdenUpdateEstado,
)
from .deps import get_db

# Crear tablas si no existen (útil en dev; en prod usar migraciones)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Tienda de Ropa — API (PostgreSQL)", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Helpers
# -----------------------------

def _orden_to_out(orden: Orden) -> OrdenOut:
    items = [
        OrdenItemOut.model_validate(i, from_attributes=True)  # type: ignore
        for i in orden.items
    ]
    total: Decimal = sum((i.subtotal for i in orden.items), start=Decimal(0))  # type: ignore
    return OrdenOut(
        id=orden.id,
        cliente_id=orden.cliente_id,
        estado=orden.estado,
        creado_en=orden.creado_en,
        items=items,
        total=total,
    )


# -----------------------------
# Rutas: Productos
# -----------------------------
@app.post("/productos", response_model=ProductoOut, status_code=status.HTTP_201_CREATED)
def crear_producto(payload: ProductoCreate, db: Session = Depends(get_db)):
    existe = db.query(Producto).filter(Producto.sku == payload.sku).first()
    if existe:
        raise HTTPException(400, detail="SKU ya existe")
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
    return query.offset(skip).limit(min(limit, 100)).all()


@app.get("/productos/{producto_id}", response_model=ProductoOut)
def obtener_producto(producto_id: int, db: Session = Depends(get_db)):
    prod = db.get(Producto, producto_id)
    if not prod:
        raise HTTPException(404, "Producto no encontrado")
    return prod


@app.put("/productos/{producto_id}", response_model=ProductoOut)
def actualizar_producto(producto_id: int, payload: ProductoUpdate, db: Session = Depends(get_db)):
    prod = db.get(Producto, producto_id)
    if not prod:
        raise HTTPException(404, "Producto no encontrado")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(prod, k, v)
    db.commit()
    db.refresh(prod)
    return prod


@app.delete("/productos/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_producto(producto_id: int, db: Session = Depends(get_db)):
    prod = db.get(Producto, producto_id)
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
    existe = db.query(Cliente).filter(Cliente.email == payload.email).first()
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
    return query.offset(skip).limit(min(limit, 100)).all()


@app.get("/clientes/{cliente_id}", response_model=ClienteOut)
def obtener_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cli = db.get(Cliente, cliente_id)
    if not cli:
        raise HTTPException(404, "Cliente no encontrado")
    return cli


@app.put("/clientes/{cliente_id}", response_model=ClienteOut)
def actualizar_cliente(cliente_id: int, payload: ClienteUpdate, db: Session = Depends(get_db)):
    cli = db.get(Cliente, cliente_id)
    if not cli:
        raise HTTPException(404, "Cliente no encontrado")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(cli, k, v)
    db.commit()
    db.refresh(cli)
    return cli


@app.delete("/clientes/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cli = db.get(Cliente, cliente_id)
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
    cliente = db.get(Cliente, payload.cliente_id)
    if not cliente:
        raise HTTPException(400, detail="Cliente no existe")

    # Validar productos / stock
    productos_cache = {}
    for item in payload.items:
        prod = db.get(Producto, item.producto_id)
        if not prod:
            raise HTTPException(400, detail=f"Producto {item.producto_id} no existe")
        if prod.stock < item.cantidad:
            raise HTTPException(400, detail=f"Stock insuficiente para SKU {prod.sku}")
        productos_cache[item.producto_id] = prod

    # Crear orden + ítems, descontar stock
    orden = Orden(cliente_id=payload.cliente_id)
    db.add(orden)
    db.flush()  # obtiene orden.id

    for item in payload.items:
        prod = productos_cache[item.producto_id]
        precio = Decimal(str(prod.precio))  # asegurar Decimal
        subtotal = precio * item.cantidad
        prod.stock -= item.cantidad
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
    return _orden_to_out(orden)


@app.get("/ordenes", response_model=List[OrdenOut])
def listar_ordenes(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
    estado: Optional[OrderStatus] = None,
    cliente_id: Optional[int] = None,
):
    query = db.query(Orden)
    if estado:
        query = query.filter(Orden.estado == estado)
    if cliente_id:
        query = query.filter(Orden.cliente_id == cliente_id)
    ordenes = query.order_by(Orden.creado_en.desc()).offset(skip).limit(min(limit, 100)).all()
    return [_orden_to_out(o) for o in ordenes]


@app.get("/ordenes/{orden_id}", response_model=OrdenOut)
def obtener_orden(orden_id: int, db: Session = Depends(get_db)):
    orden = db.get(Orden, orden_id)
    if not orden:
        raise HTTPException(404, "Orden no encontrada")
    return _orden_to_out(orden)


@app.put("/ordenes/{orden_id}/estado", response_model=OrdenOut)
def actualizar_estado_orden(orden_id: int, payload: OrdenUpdateEstado, db: Session = Depends(get_db)):
    orden = db.get(Orden, orden_id)
    if not orden:
        raise HTTPException(404, "Orden no encontrada")
    orden.estado = payload.estado
    db.commit()
    db.refresh(orden)
    return _orden_to_out(orden)


@app.delete("/ordenes/{orden_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_orden(orden_id: int, db: Session = Depends(get_db)):
    orden = db.get(Orden, orden_id)
    if not orden:
        raise HTTPException(404, "Orden no encontrada")
    db.delete(orden)
    db.commit()
    return None
