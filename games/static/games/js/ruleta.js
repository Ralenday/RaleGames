// Ruleta: consume el web service propio /api/ruleta/ con fetch.
// Si JavaScript está desactivado el formulario funciona igual por GET.

(function () {
  const form = document.getElementById('form-ruleta');
  if (!form) return;

  const resultado = document.getElementById('resultado');
  const error = document.getElementById('error-ruleta');
  const boton = document.getElementById('boton-girar');
  const NOMBRES_GIRO = ['Consultando el oráculo…', 'Mezclando cartuchos…', 'Soplando el cartucho…', 'Tirando los dados…'];

  // Crea elementos con textContent: los datos de la API nunca se insertan como HTML
  function crear(etiqueta, clase, texto) {
    const el = document.createElement(etiqueta);
    if (clase) el.className = clase;
    if (texto) el.textContent = texto;
    return el;
  }

  function mostrarGirando() {
    resultado.replaceChildren();
    const caja = crear('div', 'girando');
    caja.append(crear('div', 'girando__dado', '🎲'), crear('p', '', NOMBRES_GIRO[Math.floor(Math.random() * NOMBRES_GIRO.length)]));
    resultado.append(caja);
  }

  function mostrarJuego(juego) {
    const carta = crear('div', 'resultado__carta');

    if (juego.imagen) {
      const img = crear('img');
      img.src = juego.imagen;
      img.alt = '';
      carta.append(img);
    } else {
      carta.append(crear('div', 'resultado__vacio', juego.nombre.charAt(0)));
    }

    const info = crear('div', 'resultado__info');
    const datos = [juego.generos.join(', ')];
    if (juego.horas) datos.push(`⏱ ${juego.horas} h`);
    if (juego.metacritic) datos.push(`Metacritic ${juego.metacritic}`);

    const enlace = crear('a', 'boton', 'Ver el juego');
    enlace.href = form.dataset.juego.replace('/0/', `/${encodeURIComponent(juego.id)}/`);

    const otraVez = crear('button', 'boton boton--fantasma', 'Girar otra vez');
    otraVez.type = 'button';
    otraVez.style.marginTop = '8px';
    otraVez.addEventListener('click', () => form.requestSubmit());

    info.append(crear('p', 'etiqueta', 'Hoy te toca jugar…'), crear('h2', '', juego.nombre),
                crear('p', '', datos.filter(Boolean).join(' · ')), enlace, otraVez);
    carta.append(info);
    resultado.replaceChildren(carta);
  }

  function mostrarVacio(mensaje) {
    resultado.replaceChildren(crear('p', 'vacio', mensaje));
  }

  form.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    const datos = new FormData(form);
    if (!datos.get('animo')) {
      error.textContent = 'Primero elige cómo te sientes.';
      return;
    }
    error.textContent = '';
    boton.disabled = true;
    mostrarGirando();

    const params = new URLSearchParams(datos);
    // Actualiza la URL para que el resultado se pueda compartir
    history.replaceState(null, '', `?${params}`);

    try {
      // Pequeña pausa para que se vea la animación
      const [respuesta] = await Promise.all([
        fetch(`${form.dataset.api}?${params}`, { headers: { Accept: 'application/json' } }),
        new Promise((r) => setTimeout(r, 900)),
      ]);
      const cuerpo = await respuesta.json();
      if (respuesta.ok) mostrarJuego(cuerpo);
      else if (respuesta.status === 429) mostrarVacio('Giraste demasiadas veces. Espera un poco y vuelve a intentarlo.');
      else mostrarVacio(cuerpo.detail || 'No encontramos un juego. Intenta otra vez.');
    } catch {
      mostrarVacio('No hay conexión con el servidor. Intenta de nuevo.');
    } finally {
      boton.disabled = false;
    }
  });
})();
