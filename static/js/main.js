// UI Común + Comandos de voz (Web Speech API)
(() => {
  const sidebar = document.getElementById('sidebar');
  const toggle = document.getElementById('toggleSidebar');
  if (toggle && sidebar) toggle.addEventListener('click', () => sidebar.classList.toggle('open'));

  // Validación Bootstrap
  (() => {
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
      form.addEventListener('submit', event => {
        if (!form.checkValidity()) {
          event.preventDefault(); event.stopPropagation();
        }
        form.classList.add('was-validated');
      }, false);
    });
  })();

  // --- API Login Modal (JWT) ---
  const btnApiLoginOpen = document.getElementById('btnApiLoginOpen');
  const apiJwtStatus = document.getElementById('apiJwtStatus');
  const apiUserId = document.getElementById('apiUserId');
  const btnApiLogin = document.getElementById('btnApiLogin');
  let modalApiLogin;
  if (btnApiLoginOpen) {
    const modalEl = document.getElementById('modalApiLogin');
    if (modalEl) modalApiLogin = new bootstrap.Modal(modalEl);
    btnApiLoginOpen.addEventListener('click', ()=>{ modalApiLogin?.show(); });
  }
  function refreshApiStatus(){
    const token = localStorage.getItem('jwt');
    if (apiJwtStatus) apiJwtStatus.textContent = token ? 'API: conectado' : 'API: sin sesión';
  }
  function clearJwt(){ localStorage.removeItem('jwt'); refreshApiStatus(); }
  function openLogin(){ try{ modalApiLogin?.show(); }catch{} }
  async function ensureAuthOrPrompt(res){
    if (res && res.status === 401) { clearJwt(); flash('Sesión API expirada. Inicia de nuevo.', 'warning', 3000); openLogin(); }
    return res;
  }
  window.ApiAuth = { refreshApiStatus, clearJwt, openLogin, ensureAuthOrPrompt };
  refreshApiStatus();
  btnApiLogin?.addEventListener('click', async ()=>{
    const uid = (apiUserId?.value||'').trim();
    if(!uid){ apiUserId?.focus(); return; }
    try{
      const res = await fetch('/api/auth',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:uid})});
      if(!res.ok){ flash('No se pudo iniciar sesión API', 'warning'); return; }
      const data = await res.json();
      if(data?.access_token){ localStorage.setItem('jwt', data.access_token); flash('Sesión API iniciada', 'success', 2000); refreshApiStatus(); modalApiLogin?.hide(); }
    }catch(e){ flash('Error en autenticación API', 'danger'); }
  });

  // Helper: alerta Bootstrap
  function flash(msg, type='info', timeout=3000){
    const cont = document.querySelector('main .container-fluid') || document.body;
    const div = document.createElement('div');
    div.className = `alert alert-${type} alert-dismissible fade show`;
    div.role = 'alert';
    div.innerHTML = `${msg}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
    cont.prepend(div);
    if(timeout) setTimeout(()=>{
      try { div.classList.remove('show'); div.addEventListener('transitionend', ()=>div.remove(), {once:true}); } catch{}
    }, timeout);
  }

  // Web Speech API - comandos simples
  const btnVoice = document.getElementById('btnVoice');
  const supported = ('webkitSpeechRecognition' in window) || ('SpeechRecognition' in window);
  if (!supported) {
    if (btnVoice){ 
      btnVoice.disabled = true; 
      btnVoice.title = 'Voz no soportada por este navegador';
      btnVoice.classList.add('btn-outline-secondary');
    }
    console.warn('Web Speech API no disponible en este navegador');
    return;
  }
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const rec = new SpeechRecognition();
  rec.lang = 'es-ES';
  rec.interimResults = false; rec.maxAlternatives = 1;

  let activo = false;
  function setListeningState(on){
    activo = on;
    if(btnVoice){
      btnVoice.classList.toggle('active', on);
      btnVoice.innerHTML = on ? '<i class="bi bi-mic-mute"></i>' : '<i class="bi bi-mic"></i>';
      btnVoice.title = on ? 'Detener voz' : 'Comandos de voz';
    }
  }
  function toggleVoz(){
    try{
      if (!activo) { rec.start(); setListeningState(true); flash('🎤 Escuchando...', 'info', 1500); }
      else { rec.stop(); setListeningState(false); flash('🔇 Voz desactivada', 'secondary', 1500); }
    }catch(e){
      console.warn('No se pudo iniciar voz', e); flash('No se pudo iniciar reconocimiento de voz', 'warning');
    }
  }
  btnVoice?.addEventListener('click', toggleVoz);

  rec.onstart = () => { /* iniciado */ };
  rec.onend = () => { if (activo) { try{ rec.start(); }catch{} } };
  rec.onerror = (e) => {
    console.error('Error reconocimiento de voz:', e.error);
    setListeningState(false);
    
    if (e.error === 'not-allowed' || e.error === 'service-not-allowed') {
      flash('❌ Permiso de micrófono denegado. Por favor, habilita el acceso al micrófono en tu navegador.', 'danger', 6000);
    } else if (e.error === 'no-speech') {
      flash('⚠️ No se detectó voz. Intenta hablar más cerca del micrófono.', 'warning', 4000);
    } else if (e.error === 'audio-capture') {
      flash('❌ No se pudo acceder al micrófono. Verifica que esté conectado.', 'danger', 5000);
    } else if (e.error === 'network') {
      flash('❌ Error de red. Verifica tu conexión a internet.', 'danger', 5000);
    } else {
      flash(`⚠️ Error en reconocimiento de voz: ${e.error}`, 'warning', 4000);
    }
  };

  rec.onresult = async (ev) => {
    const texto = ev.results[0][0].transcript.toLowerCase();
    console.log('Comando:', texto);
    const token = localStorage.getItem('jwt');
    if (token) {
      try {
        const res = await fetch('/api/voz/comando', {
          method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
          body: JSON.stringify({ comando: texto })
        });
        const data = await res.json();
        if (data?.mensaje) flash(data.mensaje, data.exito? 'success':'warning', 4000);
        
        // Ejecutar acciones específicas
        if (data?.accion) {
          switch(data.accion) {
            case 'navegar':
              if (data.url) setTimeout(() => window.location.href = data.url, 1000);
              break;
            case 'crear_equipo':
              flash('💡 Tip: Use el botón "Nuevo" en la página de equipos para crear equipos', 'info', 3000);
              break;
            case 'crear_reserva':
              flash('💡 Tip: Use el botón "Reservar" junto a cada equipo', 'info', 3000);
              break;
            case 'ajustar_stock':
              flash('💡 Tip: Vaya a inventario para ajustar cantidades', 'info', 3000);
              break;
          }
        }
      } catch (e) { console.error(e); flash('Error enviando comando', 'danger'); }
    } else {
      // Comandos básicos sin JWT
      if (texto.includes('equipos') || texto.includes('ir a equipos')) window.location.href = '/equipos';
      else if (texto.includes('inventario') || texto.includes('ir a inventario')) window.location.href = '/inventario';
      else if (texto.includes('reservas') || texto.includes('ir a reservas')) window.location.href = '/reservas';
      else if (texto.includes('dashboard') || texto.includes('inicio')) window.location.href = '/dashboard';
      else if (texto.includes('ayuda')) flash("Comandos básicos: 'ir a equipos', 'ir a inventario', 'ir a reservas', 'ir a dashboard'. Para CRUD inicie sesión API.", 'info', 4000);
      else flash('Comando no reconocido. Inicie sesión API para más comandos.', 'warning');
    }
  };
})();
