import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function App() {
  const [view, setView] = useState("inicio");

  const renderView = () => {
    switch (view) {
      case "inicio":
        return (
          <div className="space-y-4">
            <h1 className="text-2xl font-bold">Productos destacados y descuentos</h1>
            <p>Aquí se mostrarán los más vendidos y descuentos dinámicos.</p>
            <Button onClick={() => setView("presentacion")}>
              Presentación de la empresa
            </Button>
          </div>
        );
      case "presentacion":
        return (
          <div className="space-y-4">
            <h1 className="text-2xl font-bold">Presentación de la empresa</h1>
            <ul className="list-disc pl-5">
              <li>Quiénes somos</li>
              <li>Sala de prensa</li>
              <li>Métodos de contacto</li>
              <li>Preguntas frecuentes</li>
              <li>Redes sociales</li>
            </ul>
            <Button onClick={() => setView("busqueda")}>
              Ir a búsqueda de productos
            </Button>
          </div>
        );
      case "busqueda":
        return (
          <div className="space-y-4">
            <h1 className="text-xl font-bold">Barra de búsqueda</h1>
            <input
              className="border p-2 rounded w-full"
              placeholder="Buscar productos..."
              onKeyDown={(e) => e.key === "Enter" && setView("catalogo")}
            />
            <Button onClick={() => setView("catalogo")}>Ver catálogo</Button>
          </div>
        );
      case "catalogo":
        return (
          <div className="grid grid-cols-4 gap-4">
            <div className="col-span-1 space-y-2">
              <h2 className="font-bold">Filtros</h2>
              <ul>
                <li>Tipo de prenda</li>
                <li>Rango de precio</li>
                <li>Envío gratis</li>
              </ul>
            </div>
            <div className="col-span-3 grid grid-cols-2 gap-2">
              {["Producto 1", "Producto 2", "Producto 3"].map((p, i) => (
                <Card key={i}>
                  <CardContent className="p-4">
                    <h3>{p}</h3>
                    <Button onClick={() => setView("carrito")}>
                      Agregar al carrito
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        );
      case "carrito":
        return (
          <div className="space-y-4">
            <h1 className="text-xl font-bold">Carrito de compras</h1>
            <p>Aquí podrás modificar y eliminar productos (pendiente en otros issues).</p>
            <Button onClick={() => setView("login")}>Ir a inicio de sesión</Button>
          </div>
        );
      case "login":
        return (
          <div className="space-y-4">
            <h1 className="text-xl font-bold">Iniciar sesión / Registro</h1>
            <input className="border p-2 rounded w-full" placeholder="Usuario" />
            <input
              className="border p-2 rounded w-full"
              placeholder="Contraseña"
              type="password"
            />
            <Button>Ingresar</Button>
            <p className="text-sm">
              O regístrate con servicios externos o manualmente.
            </p>
            <Button onClick={() => setView("contacto")}>
              Ir a sección de contacto
            </Button>
          </div>
        );
      case "contacto":
        return (
          <div className="space-y-4">
            <h1 className="text-xl font-bold">Sección de contacto</h1>
            <p>
              Aquí se desplegará un chat al lado de la vista (pendiente en otros
              issues).
            </p>
            <Button onClick={() => setView("inicio")}>Volver al inicio</Button>
          </div>
        );
      default:
        return <p>Vista no encontrada</p>;
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6 flex space-x-2">
        <Button onClick={() => setView("inicio")}>Inicio</Button>
        <Button onClick={() => setView("presentacion")}>Empresa</Button>
        <Button onClick={() => setView("busqueda")}>Buscar</Button>
        <Button onClick={() => setView("catalogo")}>Catálogo</Button>
        <Button onClick={() => setView("carrito")}>Carrito</Button>
        <Button onClick={() => setView("login")}>Login</Button>
        <Button onClick={() => setView("contacto")}>Contacto</Button>
      </div>
      {renderView()}
    </div>
  );
}