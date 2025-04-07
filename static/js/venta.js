// Precios de las galletas
const precios = {
    mantequilla: 4.5,
    avena: 4.5,
    coco: 4.5,
    almendra: 4.5,
    chocolate: 4.5,
    mani: 4.5,
    maicena: 4.5,
    vainilla: 4.5,
    miel: 4.5,
    especial: 4.5,
};

// Variables generales
const cantidadInput = document.getElementById('cantidad');
const galletaSelect = document.getElementById('galleta');
const tipoVentaSelect = document.getElementById('tipo_venta');
const precioLabel = document.getElementById('precio');
const tableBody = document.getElementById('grupo-table-body');
const preciot = document.getElementById('preciot')

// Función para calcular el precio total basado en el tipo de venta
function actualizarPrecio() {
    const cantidad = parseFloat(cantidadInput.value) || 0;
    const galleta = galletaSelect.value;
    const tipoVenta = tipoVentaSelect.value;
    const precioPorGalleta = precios[galleta] || 0;

    let totalPrecio = 0;
    let cantidadGalletas = 0;

    if (tipoVenta === "unidad") {
        totalPrecio = cantidad * precioPorGalleta;
        cantidadGalletas = cantidad;
    } else if (tipoVenta === "peso") {
        cantidadGalletas = Math.floor((cantidad * 1000) / 35); // Convertir kilos a gramos
        totalPrecio = cantidadGalletas * precioPorGalleta;
    } else if (tipoVenta === "precio") {
        cantidadGalletas = Math.floor(cantidad / precioPorGalleta);
        totalPrecio = cantidadGalletas * precioPorGalleta;
    } else if (tipoVenta === "paquete") {
        cantidadGalletas = cantidad * 10;
        totalPrecio = cantidadGalletas * precioPorGalleta;
    }
    // Actualizar el precio en la etiqueta
    precioLabel.textContent = `Total: $${totalPrecio.toFixed(2)} (${cantidadGalletas} galletas)`;
    preciot.value = totalPrecio.toFixed(2);
}

// Función para agregar a la tabla
function agregarAlCarrito() {
    const cantidad = parseFloat(cantidadInput.value) || 0;
    const galleta = galletaSelect.value;
    const tipoVenta = tipoVentaSelect.value;

    if (cantidad <= 0) {
        Swal.fire({
            icon: 'error',
            title: 'Oops...',
            text: 'Por favor ingresa una cantidad válida.'
        });
        return;
    }

    // Calcular cantidad de galletas según tipo de venta
    let cantidadGalletas = 0;
    if (tipoVenta === "unidad") {
        cantidadGalletas = cantidad;
    } else if (tipoVenta === "peso") {
        cantidadGalletas = Math.floor((cantidad * 1000) / 35);
    } else if (tipoVenta === "precio") {
        const precioPorGalleta = precios[galleta] || 0;
        cantidadGalletas = Math.floor(cantidad / precioPorGalleta);
    } else if (tipoVenta === "paquete") {
        cantidadGalletas = cantidad * 10;
    }
}

// Eventos
//document.querySelector('.btn-add').addEventListener('click', agregarAlCarrito);
//document.querySelector('.btn-warning:nth-child(2)').addEventListener('click', realizarVenta);
cantidadInput.addEventListener('input', actualizarPrecio);
galletaSelect.addEventListener('change', actualizarPrecio);
tipoVentaSelect.addEventListener('change', actualizarPrecio);
