📄 Read this in [English](README_EN.md)
# 🇺🇸 Reprogramador de Citas Visa USA - Colombia  

Este proyecto es un bot automatizado para reprogramar citas de visa americana en [usvisa-info.com](https://usvisa-info.com). Permite reagendar tanto la **cita consular** como la **cita CAS** a una fecha y hora más conveniente.  

## 📌 Requisitos previos  
- Contar con una **cita de visa de EE.UU. ya programada**.  
- [Opcional] Tener un **API Token** de **Pushover** y/o **SendGrid** para recibir notificaciones.  
  - También puedes usar el archivo **esender.php** de este repositorio para enviar notificaciones por correo desde tu sitio web.  

## ⚠️ Información importante  
- Este bot está **adaptado para Colombia** y ha sido probado con éxito para reagendar citas en **febrero de 2025**.  
- Para usarlo en otros países, debes modificar la lista de embajadas compatibles en el archivo **embassy.py**.  

### ➕ Agregar una nueva embajada  
Para añadir una embajada, necesitas obtener su **"facility id"** siguiendo estos pasos:  

1. En **Google Chrome**, accede a la página de reserva de citas en tu cuenta.  
2. Haz **clic derecho** en la sección de ubicación y selecciona **"Inspeccionar"**.  
3. Se abrirá una ventana con el código HTML resaltando un elemento `<select>`.  
4. Busca el **facility id** y agrégalo al archivo **embassy.py**.  
5. Si hay varias embajadas con diferentes **facility id**, puedes agregarlas también.  

📷 **Ejemplo visual:**  
![Cómo encontrar el Facility ID](https://github.com/Soroosh-N/us_visa_scheduler/blob/main/_img.png?raw=true)  

---

## ⚙️ Configuración inicial  
1. **Instalar dependencias**:  
   - [Google Chrome](https://www.google.com/chrome/)  
   - [Python 3](https://www.python.org/downloads/)
   - [ChromeDriver](https://developer.chrome.com/docs/chromedriver/downloads?hl=es-419)

2. **Configurar el entorno virtual e instalar las dependencias**:  
   - **En Windows**:  
     - Ejecuta el archivo `setup.bat`.  
   - **En Linux**:  
     - Otorga permisos de ejecución con:  
       ```bash
       chmod +x setup.sh
       ```  
     - Ejecuta el script:  
       ```bash
       ./setup.sh
       ```  

   - **Instalación manual** (opcional):  
     ```bash
     python3 -m venv venv  
     source venv/bin/activate  # En Windows: venv\Scripts\activate  
     pip install --upgrade pip  # En Windows: python.exe -m pip install --upgrade pip
     pip install -r requirements.txt  
     ```

---

## ▶️ Cómo usar  
1. Completa la configuración inicial.  
2. Edita el archivo **config.ini.example**, guarda los cambios y renómbralo a **config.ini**.  
3. [Opcional] Configura las notificaciones push en **config.ini**.  
4. [Opcional] Modifica la configuración de notificaciones web en **config.ini** y **esender.php**.  
5. Ejecuta el bot con:  
   ```bash
   python3 visa.py
   ```

---

## 🚀 Próximas mejoras (TODO)  
- Optimizar tiempos de ejecución (**evitar bloqueos y mejorar rendimiento**).  
- Crear una **interfaz gráfica (GUI)** con **PyQt**.  
- Soporte para **múltiples cuentas** (alternar entre cuentas en períodos de descanso).  
- Mejorar las alertas sonoras para distintos eventos.  
- Ampliar la lista de embajadas compatibles.  

---

## 💙 Agradecimientos  
Gracias a **@yaojialyu** por el script original, y a **@uxDaniel, @cejaramillof, y @Soroosh-N** por sus contribuciones y mejoras. ¡Este proyecto no sería posible sin ustedes! 🚀  

---

### 🌎 **📌 Notas finales**  
Este bot fue desarrollado para ayudar a usuarios en Colombia con el proceso de reprogramación de citas de visa americana. Si deseas adaptarlo a otro país, revisa la sección de embajadas y haz los cambios necesarios.

Si tienes sugerencias o mejoras, ¡las contribuciones son bienvenidas! ✨