# Pantalla manual — versión para probar en hardware

Base exacta: `firmware-final-v1.0`, commit `3ec3fde8ed6a621024185886caa71225e4bf3d95`.
Archivo activo: **Firmware_BLE.ino**. Los demás `.ino` históricos no se modificaron.
Android compañero: `LucianoRodriguezUrquiza/APK-PPG`, rama `screen-control-sleep-v1`.

## Carga

Abrir únicamente `Firmware_BLE.ino` con Arduino IDE y aceptar crear la carpeta
`Firmware_BLE`. No compilar juntos los otros `.ino` del repositorio.
Usar Waveshare ESP32-S3-LCD-1.47B, Arduino-ESP32 3.3.12, Flash 16 MB, PSRAM OPI,
USB CDC On Boot habilitado y partición `app3M_fat9M_16MB`, como en el workflow.
Las versiones de bibliotecas están fijadas en `.github/workflows/screen-control-validation.yml`.

## Cambios acotados

- Escala matemática 0,8 en X/Y del corazón, en ambos estados del latido, alrededor
  del centro original (42,59). Reflejos escalados con el mismo factor. Las posiciones
  y dimensiones del resto de la interfaz quedan intactas. La rasterización redondea
  a píxeles enteros, por lo que las dimensiones medidas en píxeles no admiten siempre
  una reducción decimal exacta. Límites normal: (7,21)-(77,90) → (14,29)-(70,83).
  Latido grande: (4,19)-(80,92) → (12,27)-(72,85).
- El archivo original de esta rama no contiene una línea ECG blanca dentro del
  corazón: contiene reflejos. Se conservó ese diseño sin añadir uno distinto.
- Sin temporizador ni acción de BOOT para la retroiluminación. Enciende al arrancar.
- GPIO46 se modifica en la tarea BLE, nunca en el callback de recepción. Sólo cambia
  la retroiluminación: adquisición, procesamiento, LCD y BLE siguen ejecutándose.

## Contrato BLE añadido

Se conservan todos los UUID, formatos de telemetría, frecuencias y negociación `HELLO:2`.
En RX NUS, después de negociar v2:

| Orden | Respuesta por TX NUS, terminada en LF |
|---|---|
| `SCREEN:ON` | `ACK:SCREEN:ON` después de aplicar HIGH a GPIO46 |
| `SCREEN:OFF` | `ACK:SCREEN:OFF` después de aplicar LOW a GPIO46 |
| `SCREEN:GET` | `ACK:SCREEN:ON` o `ACK:SCREEN:OFF`, sin modificar GPIO46 |

Las órdenes son idempotentes. Se descartan órdenes de épocas BLE anteriores.
La desconexión no cambia la retroiluminación; el advertising/reconexión conserva
su lógica original. Android consulta el estado después de cada negociación.
El ACK confirma el estado aplicado al GPIO, no una medición óptica de la pantalla.

## Verificación

- `python tools/verify_screen.py`: compila y ejecuta en C++ el manejador real extraído
  del sketch, con GPIO/transporte simulados. Prueba ON/OFF/GET, reintentos, arranque,
  épocas, reconexión y órdenes previas.
- Comparación contra la base: todo el código ajeno a inicialización de pantalla,
  dos funciones de dibujo del corazón, manejador de órdenes y llamada al temporizador
  permanece idéntico.
- Compilación real ESP32-S3: GitHub Actions, ejecución `40202727901`, exitosa.

Pruebas físicas pendientes: visibilidad bajo el marco; mantener encendido varios
minutos; apagar/encender desde Android; verificar BPM, PPG, IMU y registros con luz
apagada; desconectar/reconectar estando apagada y recuperar el encendido; reiniciar
y comprobar encendido inicial. No se dispone aquí del reloj ni del teléfono real.
