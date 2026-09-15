# Indicaciones para el proyecto

1. Analiza todo el proyecto, e  ignora la carpeta old/
2. Ordenar la carpeta app/ de IPFramework, manteniendo la compatibilidad con el funcionamiento actual del proyecto y teneindo en cuenta las siguientes idicaciones:
    - Todo lo realcionado con la comunicacion serial del arduino estará en un unico archivo llamado serial.py
    - Todo lo relacionado con la comunicacion con el frontend estará en un unico archivo llamado routes.y
    - Todas las comprobaciones, chequeos de estados etc, estarán en un unico archivo llamado states.py
    - Debe haber un unico archivo llamado control.py, que garantice que la seleccion del "Controlador" en el frontend se aplique
    - Todos los tipos de controladores, estaŕan en una carpeta llamada control/
    - En la carpeta control/ debe haber un unico archivo llamado config.py, este archivo debe tener las configuraciones de los controladores (Las recibe de cotrol.py), para este caso, como solo está lqr, ese archivo debe tener las ganacias lqr
    - Actualmente solo hay lqr, por ende todo lo relacionado con ese control debe estar en un unico archivo llamado lqr.py en la carpeta control/
    - El archivo control.py hace la selección del controlador con condiconales de acuerdo al controlador que sea selecionado en el frontend. De esa forma si se selecciona lqr + Swing-up, el control.py solo lee al archivo lqr.py, y no a otro, a menos que otro cotrol sea seleccionado

Esta estructura es una referencia inicial. Si el análisis demuestra que algún archivo adicional es necesario para mantener una separación adecuada de responsabilidades, justifica su incorporación antes de modificar la estructura.