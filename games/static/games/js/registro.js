// Validación del registro en el navegador: da retroalimentación inmediata.
// El servidor (forms.py) vuelve a validar todo, esto solo mejora la experiencia.

(function () {
  const form = document.getElementById('form-registro');
  if (!form) return;

  const campos = {
    username: form.querySelector('#id_username'),
    email: form.querySelector('#id_email'),
    plataforma: form.querySelector('#id_plataforma'),
    password1: form.querySelector('#id_password1'),
    password2: form.querySelector('#id_password2'),
    terminos: form.querySelector('#id_terminos'),
  };

  const reglasPassword = {
    largo: (p) => p.length >= 8,
    letra: (p) => /[A-Za-z]/.test(p),
    numero: (p) => /\d/.test(p),
    usuario: (p) => p.length > 0 && !p.toLowerCase().includes(campos.username.value.toLowerCase() || '\u0000'),
  };

  // Cada validador devuelve un mensaje de error o '' si el valor es correcto
  const validadores = {
    username(v) {
      if (!v) return 'Escribe tu gamertag.';
      if (!/^[A-Za-z0-9_]{3,20}$/.test(v)) return 'Usa de 3 a 20 caracteres: letras, números o guion bajo.';
      return '';
    },
    email(v) {
      if (!v) return 'Escribe tu correo.';
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v)) return 'Ese correo no parece válido.';
      return '';
    },
    plataforma(v) {
      return v ? '' : 'Elige tu plataforma favorita.';
    },
    password1(v) {
      const fallas = Object.entries(reglasPassword).filter(([, regla]) => !regla(v));
      return fallas.length ? 'La contraseña no cumple todos los requisitos.' : '';
    },
    password2(v) {
      if (!v) return 'Confirma tu contraseña.';
      return v === campos.password1.value ? '' : 'Las contraseñas no coinciden.';
    },
    terminos() {
      return campos.terminos.checked ? '' : 'Debes aceptar para crear tu cuenta.';
    },
  };

  function mostrar(nombre, mensaje) {
    const contenedor = campos[nombre].closest('.campo');
    contenedor.querySelector(`[data-error="${nombre}"]`).textContent = mensaje;
    contenedor.classList.toggle('invalido', !!mensaje);
    contenedor.classList.toggle('valido', !mensaje && nombre !== 'terminos');
  }

  function validar(nombre) {
    const mensaje = validadores[nombre](campos[nombre].value.trim());
    mostrar(nombre, mensaje);
    return !mensaje;
  }

  function actualizarFuerza() {
    const p = campos.password1.value;
    let cumplidas = 0;
    for (const [nombre, regla] of Object.entries(reglasPassword)) {
      const ok = regla(p);
      if (ok) cumplidas++;
      document.querySelector(`#requisitos [data-regla="${nombre}"]`).classList.toggle('ok', ok);
    }
    // Puntos extra por largo y símbolos
    let puntos = cumplidas;
    if (p.length >= 12) puntos++;
    if (/[^A-Za-z0-9]/.test(p)) puntos++;

    const barra = document.getElementById('fuerza-barra');
    const porcentaje = Math.min(100, (puntos / 6) * 100);
    barra.style.width = porcentaje + '%';
    barra.style.background = porcentaje < 50 ? 'var(--rojo)' : porcentaje < 80 ? 'var(--ambar)' : 'var(--menta)';
  }

  // Valida al salir del campo y, si ya marcó error, mientras escribe
  for (const nombre of Object.keys(campos)) {
    const campo = campos[nombre];
    const evento = campo.type === 'checkbox' || campo.tagName === 'SELECT' ? 'change' : 'blur';
    campo.addEventListener(evento, () => validar(nombre));
    campo.addEventListener('input', () => {
      if (campo.closest('.campo').classList.contains('invalido')) validar(nombre);
    });
  }

  campos.password1.addEventListener('input', () => {
    actualizarFuerza();
    if (campos.password2.value) validar('password2');
  });
  campos.username.addEventListener('input', actualizarFuerza);

  form.addEventListener('submit', (evento) => {
    const resultados = Object.keys(campos).map(validar);
    if (resultados.includes(false)) {
      evento.preventDefault();
      form.querySelector('.invalido input, .invalido select')?.focus();
    }
  });

  actualizarFuerza();
})();
