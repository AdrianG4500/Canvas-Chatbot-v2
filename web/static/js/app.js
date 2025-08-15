// Configuración del parser Marked.js
marked.setOptions({
    gfm: true,
    breaks: true,
    smartLists: true,
    smartypants: true
});

// Variables globales
let contadorPreguntas = 0;
let currentTheme = 'light';

/**
 * Inicialización del tema
 */
function initTheme() {
    // Verificar preferencia guardada en localStorage
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    currentTheme = savedTheme || (prefersDark ? 'dark' : 'light');
    applyTheme(currentTheme);
}

/**
 * Aplicar tema seleccionado
 * @param {string} theme - 'light' o 'dark'
 */
function applyTheme(theme) {
    const html = document.documentElement;
    const themeIcon = document.getElementById('theme-icon');
    const themeText = document.getElementById('theme-text');
    const logo = document.getElementById('logo');
    
    if (theme === 'dark') {
        html.setAttribute('data-theme', 'dark');
        themeIcon.textContent = '🌙';
        themeText.textContent = 'Modo Oscuro';
        if (logo) {
            logo.src = logo.src.replace('logo.png', 'logo_dark.png');
        }
    } else {
        html.setAttribute('data-theme', 'light');
        themeIcon.textContent = '☀️';
        themeText.textContent = 'Modo Claro';
        if (logo) {
            logo.src = logo.src.replace('logo_dark.png', 'logo.png');
        }
    }
    
    currentTheme = theme;
    localStorage.setItem('theme', theme);
}

/**
 * Toggle entre temas claro y oscuro
 */
function toggleTheme() {
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    applyTheme(newTheme);
}

/**
 * Configurar el toggle de tema
 */
function configurarToggleTema() {
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
}

/**
 * Función para crear un nuevo contenedor de pregunta-respuesta
 * @param {string} preguntaTexto - El texto de la pregunta
 * @param {string} consultaId - ID único de la consulta
 * @returns {HTMLElement} - El elemento creado
 */
function crearNuevoQA(preguntaTexto, consultaId) {
    contadorPreguntas++;
    const timestamp = new Date().toLocaleString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    
    const qaItem = document.createElement('div');
    qaItem.className = 'qa-item nueva-pregunta';
    qaItem.id = `qa-${consultaId}`;
    qaItem.setAttribute('data-consulta-id', consultaId);
    
    // Escapar HTML para evitar XSS
    const preguntaEscapada = preguntaTexto
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    
    qaItem.innerHTML = `
        <div class="pregunta-container">
            <div class="pregunta-header">
                <strong>💬 Pregunta #${contadorPreguntas}</strong>
                <span class="pregunta-timestamp">${timestamp}</span>
            </div>
            <div class="pregunta-texto">${preguntaEscapada}</div>
        </div>
        <div class="respuesta-container">
            <div class="respuesta-status status-loading">
                <span class="loader">🤔 Procesando tu pregunta</span>
            </div>
            <div class="respuesta-contenido" style="display: none;"></div>
            <div class="fuentes-container" style="display: none;"></div>
        </div>
    `;
    
    // Agregar al historial (más reciente arriba)
    const historialContainer = document.getElementById('historial-container');
    historialContainer.insertBefore(qaItem, historialContainer.firstChild);
    
    // Scroll suave al nuevo elemento
    setTimeout(() => {
        qaItem.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start',
            inline: 'nearest'
        });
    }, 100);
    
    return qaItem;
}

/**
 * Función para actualizar el estado de una consulta específica
 * @param {string} consultaId - ID de la consulta
 * @param {Object} data - Datos de la respuesta
 */
function actualizarEstadoConsulta(consultaId, data) {
    const qaItem = document.getElementById(`qa-${consultaId}`);
    if (!qaItem) {
        console.warn(`No se encontró el elemento qa-${consultaId}`);
        return;
    }
    
    const statusDiv = qaItem.querySelector('.respuesta-status');
    const contenidoDiv = qaItem.querySelector('.respuesta-contenido');
    const fuentesDiv = qaItem.querySelector('.fuentes-container');
    
    if (data.error) {
        statusDiv.innerHTML = `<span class="status-error">❌ Error: ${data.error}</span>`;
        return;
    }
    
    if (data.estado === "completado") {
        statusDiv.innerHTML = '<span class="status-completed">✅ Respuesta completada</span>';
        
        // Mostrar respuesta con formato Markdown y animación
        try {
            const respuestaHtml = marked.parse(data.respuesta || 'Sin respuesta disponible.');
            contenidoDiv.innerHTML = respuestaHtml;
            contenidoDiv.style.display = 'block';
            
            // Trigger de animación con slight delay para suavidad
            setTimeout(() => {
                contenidoDiv.classList.add('revealed');
            }, 50);
            
        } catch (error) {
            console.error('Error al procesar Markdown:', error);
            contenidoDiv.innerHTML = '<p>Error al procesar la respuesta.</p>';
            contenidoDiv.style.display = 'block';
            setTimeout(() => {
                contenidoDiv.classList.add('revealed');
            }, 50);
        }
        
        // Mostrar fuentes si existen con animación
        if (data.fuentes && Array.isArray(data.fuentes) && data.fuentes.length > 0) {
            const fuentesHtml = `
                <details>
                    <summary>📄 Fuentes consultadas (${data.fuentes.length})</summary>
                    <ul>
                        ${data.fuentes.map(fuente => `<li><code>${fuente}</code></li>`).join('')}
                    </ul>
                </details>
            `;
            fuentesDiv.innerHTML = fuentesHtml;
            fuentesDiv.style.display = 'block';
            
            // Animación de las fuentes con delay adicional
            setTimeout(() => {
                fuentesDiv.classList.add('revealed');
            }, 150);
        }
        
    } else if (data.estado === "error") {
        statusDiv.innerHTML = `<span class="status-error">❌ ${data.respuesta || 'Error desconocido'}</span>`;
        
    } else if (data.estado === "procesando") {
        statusDiv.innerHTML = '<span class="status-loading"><span class="loader">🔄 Generando respuesta</span></span>';
    }
}

/**
 * Función para iniciar polling de una consulta específica
 * @param {string} consultaId - ID de la consulta a monitorear
 */
function iniciarPolling(consultaId) {
    console.log(`🔍 Iniciando polling para consulta: ${consultaId}`);
    
    let intentos = 0;
    const maxIntentos = 60; // 3 minutos máximo (60 * 3 segundos)
    
    const poll = setInterval(() => {
        intentos++;
        
        if (intentos > maxIntentos) {
            console.error(`⏰ Timeout para consulta ${consultaId}`);
            const qaItem = document.getElementById(`qa-${consultaId}`);
            if (qaItem) {
                const statusDiv = qaItem.querySelector('.respuesta-status');
                statusDiv.innerHTML = '<span class="status-error">⏰ Tiempo de espera agotado</span>';
            }
            clearInterval(poll);
            return;
        }
        
        fetch(`/estado_consulta/${consultaId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                console.log(`📩 Respuesta para ${consultaId} (intento ${intentos}):`, data);
                
                actualizarEstadoConsulta(consultaId, data);
                
                // Detener polling si está completado o tiene error
                if (data.estado === "completado" || data.estado === "error" || data.error) {
                    console.log(`✅ Polling completado para ${consultaId}`);
                    clearInterval(poll);
                }
            })
            .catch(error => {
                console.error(`📡 Error en polling para ${consultaId} (intento ${intentos}):`, error);
                
                // Solo mostrar error después de varios intentos fallidos
                if (intentos > 5) {
                    const qaItem = document.getElementById(`qa-${consultaId}`);
                    if (qaItem) {
                        const statusDiv = qaItem.querySelector('.respuesta-status');
                        statusDiv.innerHTML = '<span class="status-error">📡 Error de conexión</span>';
                    }
                    clearInterval(poll);
                }
            });
    }, 3000); // Polling cada 3 segundos
}

/**
 * Obtener el ID del asistente seleccionado
 * @returns {string} - ID del asistente
 */
function obtenerAsistenteId() {
    const selectElement = document.getElementById('asistente_id');
    const hiddenElement = document.getElementById('asistente_id_hidden');
    
    if (selectElement) {
        return selectElement.value;
    } else if (hiddenElement) {
        return hiddenElement.value;
    }
    
    console.warn('No se pudo obtener el ID del asistente');
    return '';
}

/**
 * Manejo del envío del formulario de pregunta
 */
function configurarFormulario() {
    const formulario = document.getElementById('form-pregunta');
    const textArea = document.getElementById('textarea-pregunta');
    const submitButton = formulario.querySelector('button[type="submit"]');
    
    if (!formulario || !textArea || !submitButton) {
        console.error('No se encontraron elementos necesarios del formulario');
        return;
    }
    
    // Manejar envío del formulario
    formulario.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const preguntaTexto = textArea.value.trim();
        if (!preguntaTexto) {
            textArea.focus();
            return;
        }
        
        // Deshabilitar el botón temporalmente
        const originalText = submitButton.innerHTML;
        submitButton.disabled = true;
        submitButton.innerHTML = '<span>⏳ Enviando...</span>';
        
        // Preparar datos del formulario
        const formData = new FormData();
        formData.append('pregunta', preguntaTexto);
        
        // Agregar ID del asistente
        const asistenteId = obtenerAsistenteId();
        if (asistenteId) {
            formData.append('asistente_id', asistenteId);
        }
        
        // Enviar formulario
        fetch(window.location.href, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.text();
        })
        .then(html => {
            // Extraer consulta_id de la respuesta
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const consultaIdInput = doc.getElementById('consulta_id');
            
            if (consultaIdInput && consultaIdInput.value) {
                const consultaId = consultaIdInput.value;
                console.log(`✅ Nueva consulta creada: ${consultaId}`);
                
                // Crear nuevo contenedor QA
                crearNuevoQA(preguntaTexto, consultaId);
                
                // Iniciar polling para esta consulta
                iniciarPolling(consultaId);
                
                // Limpiar formulario
                textArea.value = '';
                textArea.style.height = 'auto'; // Reset altura si es redimensionable
                
            } else {
                throw new Error('No se recibió ID de consulta válido del servidor');
            }
        })
        .catch(error => {
            console.error('Error al enviar pregunta:', error);
            
            // Mostrar error al usuario
            const errorMessage = error.message.includes('HTTP') ? 
                'Error de conexión con el servidor' : 
                'Error al procesar la pregunta';
                
            alert(`❌ ${errorMessage}\n\nPor favor, verifica tu conexión e intenta de nuevo.`);
        })
        .finally(() => {
            // Rehabilitar el botón
            submitButton.disabled = false;
            submitButton.innerHTML = originalText;
        });
    });
    
    // Auto-resize del textarea
    textArea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 300) + 'px';
    });
    
    // Enviar con Ctrl+Enter o Cmd+Enter
    textArea.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            formulario.requestSubmit();
        }
    });
}

/**
 * Manejo de consulta inicial si existe
 */
function manejarConsultaInicial() {
    const consultaId = document.getElementById("consulta_id")?.value;
    const preguntaActual = document.getElementById("pregunta_actual")?.value;
    
    if (consultaId && preguntaActual) {
        console.log(`🔍 Consulta inicial detectada: ${consultaId}`);
        
        // Crear contenedor para la pregunta inicial
        crearNuevoQA(preguntaActual, consultaId);
        
        // Iniciar polling
        iniciarPolling(consultaId);
        
        // Limpiar los campos ocultos para evitar duplicación
        document.getElementById("consulta_id")?.remove();
        document.getElementById("pregunta_actual")?.remove();
    }
}

/**
 * Manejar cambios en el selector de asistentes
 */
function configurarSelectorAsistentes() {
    const select = document.getElementById('asistente_id');
    if (select) {
        select.addEventListener('change', function() {
            console.log(`Asistente seleccionado: ${this.value}`);
            // Aquí podrías agregar lógica adicional si es necesario
        });
    }
}

/**
 * Configurar atajos de teclado globales
 */
function configurarAtajosTeclado() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K para enfocar el textarea
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const textArea = document.getElementById('textarea-pregunta');
            if (textArea) {
                textArea.focus();
                textArea.select();
            }
        }
        
        // Ctrl/Cmd + Shift + L para cambiar tema
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'L') {
            e.preventDefault();
            toggleTheme();
        }
    });
}

/**
 * Mostrar indicador de carga global
 */
function mostrarIndicadorCarga() {
    // Podrías implementar un indicador de carga global aquí
    console.log('🔄 Cargando aplicación...');
}

/**
 * Ocultar indicador de carga global
 */
function ocultarIndicadorCarga() {
    console.log('✅ Aplicación cargada');
}

/**
 * Inicialización de la aplicación
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Inicializando Asistente Académico...');
    
    mostrarIndicadorCarga();
    
    try {
        // Inicializar tema
        initTheme();
        
        // Configurar funcionalidades
        configurarToggleTema();
        configurarFormulario();
        configurarSelectorAsistentes();
        configurarAtajosTeclado();
        
        // Manejar consulta inicial
        manejarConsultaInicial();
        
        console.log('✅ Asistente Académico inicializado correctamente');
        
    } catch (error) {
        console.error('❌ Error durante la inicialización:', error);
    } finally {
        ocultarIndicadorCarga();
    }
});

// Manejar errores no capturados
window.addEventListener('error', function(e) {
    console.error('❌ Error global capturado:', e.error);
});

// Manejar promesas rechazadas no capturadas
window.addEventListener('unhandledrejection', function(e) {
    console.error('❌ Promesa rechazada no capturada:', e.reason);
});