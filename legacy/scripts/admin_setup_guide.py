"""
Instrucciones para obtener tu ID de Telegram y configurarlo como admin
"""

print("""
🔍 **CÓMO OBTENER TU ID DE TELEGRAM Y CONFIGURARLO COMO ADMIN**

---

📋 **MÉTODO 1: Usar @userinfobot (Recomendado)**

1. Abre Telegram
2. Busca el bot: @userinfobot
3. Envía cualquier mensaje al bot
4. El bot responderá con tu ID de usuario

Ejemplo de respuesta:
👤 User ID: 123456789
📝 Username: @tuusername
🔗 First Name: Tu Nombre

---

📋 **MÉTODO 2: Usar @RawDataBot**

1. Abre Telegram
2. Busca el bot: @RawDataBot
3. Envía cualquier mensaje al bot
4. Busca "from" → "id" en la respuesta JSON

---

📋 **MÉTODO 3: Revisar mensajes anteriores**

Si ya has interactuado con bots antes, puedes:
1. Ir a cualquier bot que hayas usado
2. Hacer clic en "Forward" (Reenviar)
3. Seleccionar un mensaje que enviaste a ese bot
4. El ID aparecerá en el mensaje reenviado

---

⚙️ **CONFIGURACIÓN EN .env**

Una vez que tengas tu ID (ej: 123456789):

1. Abre tu archivo `.env` en la raíz del proyecto
2. Busca la línea: `ADMIN_USERS=`
3. Añade tu ID:

   **Si no existe la línea:**
   ```
   ADMIN_USERS=123456789
   ```

   **Si ya hay otros admins:**
   ```
   ADMIN_USERS=id_admin1,id_admin2,123456789
   ```

4. Guarda el archivo .env
5. Reinicia el contenedor del bot:
   ```bash
   docker-compose restart zeepubs_bot
   ```

---

🚀 **VERIFICACIÓN**

Después de reiniciar:
1. Envía `/upload_epub` respondiendo a un archivo EPUB
2. Si funciona, ya eres admin
3. Si sigue diciendo "Solo admins", revisa que el ID esté correcto

---

🔧 **TROUBLESHOOTING**

**Problema:** Sigue diciendo "Solo admins pueden usar este comando"

**Soluciones:**
1. Verifica que el ID esté correcto (sin espacios ni caracteres extra)
2. Asegúrate de guardar el archivo .env
3. Reinicia el contenedor completamente: `docker-compose down && docker-compose up -d`
4. Verifica que no haya comillas alrededor del número

**Ejemplo correcto:**
```
ADMIN_USERS=123456789
```

**Ejemplo incorrecto:**
```
ADMIN_USERS="123456789"  # ❌ Sin comillas
ADMIN_USERS= 123456789   # ❌ Sin espacios
ADMIN_USERS=123,456,789  # ❌ Sin comas si es un solo número
```

---

📞 **AYUDA ADICIONAL**

Si necesitas ayuda:
1. Obtén tu ID con @userinfobot
2. Muestra el resultado
3. Revisa tu .env para asegurar que el ID esté correcto
4. Reinicia el servicio

¡Listo! Ya deberías poder usar todos los comandos de admin. 🎉
""")
