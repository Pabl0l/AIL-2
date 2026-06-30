# AIL — Manual del Paradigma
## Parte 3: La Práctica

---

> Los protocolos son secuencias operativas. No son sugerencias. Son el procedimiento exacto para situaciones específicas.

---

## PROTOCOLO 1 — Iniciar un sistema nuevo

Este protocolo se ejecuta cuando se crea un sistema desde cero, partiendo de una especificación en lenguaje natural o un intent node.

### Fase 1: Ontología (nunca saltar este paso)

Identificar todos los conceptos del dominio que menciona la especificación. Para cada concepto:

1. Verificar si ya existe un nodo `ontology` con ese concepto en el grafo
2. Si existe: registrar su ID, continuar
3. Si no existe: crear el nodo `ontology`

Criterio para identificar un concepto: es un sustantivo que tiene significado específico en el dominio de negocio. "Producto", "Almacén", "Movimiento de stock", "Punto de reorden", "Gerente de almacén" son conceptos. "Lista", "Resultado", "Error" no lo son.

### Fase 2: Constraints (antes que cualquier código)

Para cada regla de negocio que mencione la especificación:

1. Crear un nodo `constraint`
2. Escribir el enunciado de la regla en términos del dominio (usando los términos de los nodos ontology)
3. Determinar si es verificable automáticamente (`verificable: true/false`)
4. Si es verificable: anotar que se necesitará un nodo computation de verificación (se crea en Fase 4)

No crear código aún. Solo los constraints.

### Fase 3: Datos

Para cada entidad del dominio que necesita persistencia o transporte:

1. Crear un nodo `data` con sus campos tipados
2. Agregar edges `belongs-to` a los nodos `ontology` correspondientes
3. Agregar edges `constrained-by` a los constraints que aplican al tipo de dato
4. No agregar métodos. No agregar constructores.

### Fase 4: Comportamiento

Para cada operación que el sistema debe realizar:

1. Crear un nodo `computation`
2. Definir su firma: inputs (tipos de nodos `data`), outputs (tipos de nodos `data` o eventos), efectos laterales
3. Agregar edges `depends-on` a los nodos que necesita
4. Agregar edges `constrained-by` a los constraints que debe cumplir
5. Generar la conducta IR
6. Si algún constraint de Fase 2 era verificable: crear el nodo `computation` de verificación y conectarlo al constraint

### Fase 5: Tests

Para cada nodo `computation` creado en Fase 4:

1. Crear mínimo 3 nodos `test`: caso feliz, caso de error, caso límite
2. Para cada constraint con `verificable: true`: crear al menos un nodo `test` que verifique el constraint
3. Agregar edges `tests` de los nodos `test` al nodo `computation` correspondiente

### Fase 6: Boundaries

Para cada operación que debe ser accesible externamente:

1. Crear un nodo `boundary`
2. Definir el protocolo externo (HTTP, gRPC, event stream)
3. Agregar edge `boundary-exposes` al nodo `computation` que implementa la operación
4. Agregar edges `constrained-by` a los constraints de autenticación/autorización relevantes
5. La documentación externa (OpenAPI, etc.) se genera automáticamente desde este nodo

### Fase 7: Snapshot y validación

1. Crear snapshot del estado del grafo
2. Ejecutar validación automática:
   - Consistencia de tipos en todos los edges
   - Todos los constraints verificables
   - Cobertura de tests ≥ 80%
   - Todos los boundaries con constraint de auth
3. Si pasa: snapshot tiene estado "valid"
4. Si falla: resolver problemas identificados, volver al paso pertinente

### Fase 8: Compilación (solo si snapshot es "valid")

1. Compilar el grafo desde los nodos `boundary` como entry points
2. El compilador recorre edges `depends-on` y `boundary-exposes`
3. Ensambla IR de todos los nodos `computation` alcanzables
4. Emite artefacto de despliegue (container, binario, WASM)

---

## PROTOCOLO 2 — Modificar comportamiento existente

Este protocolo se ejecuta cuando una funcionalidad existente necesita cambiar.

### Paso 1: Identificar el nodo objetivo

1. Buscar por embedding semántico si no se conoce la ID
2. Verificar que el nodo encontrado es el correcto: revisar su firma y sus edges `constrained-by`
3. Si se encontraron múltiples candidatos: seleccionar el que tiene los edges `constrained-by` más relevantes

### Paso 2: Cargar el contexto mínimo (Regla III.1)

1. El nodo objetivo
2. Sus dependencias directas (depth-1 `depends-on`)
3. Sus constraints (`constrained-by`)
4. Sus test nodes (edges `tests` entrantes)
5. Sus dependientes directos (edges `depends-on` entrantes desde otros nodos)

### Paso 3: Verificar que los constraints siguen siendo válidos

Antes de modificar la conducta: leer los constraints del nodo y verificar que el cambio planificado los satisface. Si el cambio viola un constraint existente:

- **Opción A:** Modificar el constraint (si la regla de negocio cambió). Crear nuevo nodo constraint. Actualizar edges.
- **Opción B:** Replantear el cambio para satisfacer el constraint existente.

No se puede proceder con un cambio que viola un constraint sin primero resolver esta decisión.

### Paso 4: Crear snapshot

Antes de cualquier modificación: `graph.snapshot()`.

### Paso 5: Crear nuevo nodo con conducta modificada

1. Tomar el nodo objetivo como base
2. Modificar la conducta IR (o regenerar el IR desde nueva especificación)
3. Crear nuevo nodo con la conducta modificada
4. Nuevo nodo tiene nueva ID (content-addressing)
5. Nuevo nodo tiene edge `derives-from` → nodo anterior
6. Todos los edges del nodo anterior se replican en el nuevo nodo (mismos `depends-on`, `constrained-by`, etc.)

### Paso 6: Actualizar los test nodes

1. Verificar si los test nodes existentes siguen siendo válidos para el nuevo nodo
2. Tests que ya no aplican: eliminar sus edges `tests` del nuevo nodo
3. Tests que el cambio requiere: crear nuevos nodos `test` con edges `tests` al nuevo nodo
4. Tests que no cambian: redirigir su edge `tests` al nuevo nodo

### Paso 7: Actualizar dependientes

Para cada nodo con edge `depends-on` al nodo anterior:
- Aplicar Regla IV.3: decidir si adoptan la nueva versión, mantienen la anterior, o son incompatibles

### Paso 8: Validar snapshot

1. Ejecutar validación completa del snapshot
2. Si pasa: snapshot válido, proceder
3. Si falla: los fallos indican qué nodos dependientes tienen problemas de compatibilidad. Resolver uno a uno.

---

## PROTOCOLO 3 — Agregar una regla de negocio a funcionalidad existente

Este es el caso más frecuente de mantenimiento: "a partir de ahora, X también debe cumplir Y".

### Paso 1: Verificar si el constraint ya existe

Buscar en el grafo (semánticamente) si ya existe un nodo `constraint` que exprese esta regla. Si existe y no estaba conectado: agregar edge `constrained-by`. Fin.

### Paso 2: Crear el nodo constraint (si no existe)

Crear el nodo `constraint` con su enunciado, dominio, severidad, y si es verificable.

### Paso 3: Conectar el constraint

Agregar edges `constrained-by` desde todos los nodos `computation` que deben cumplir la nueva regla.

### Paso 4: Si el constraint es verificable, crear el nodo de verificación

Crear un nodo `computation` que implementa la verificación. Conectarlo al constraint con el campo `nodo_verificacion`.

### Paso 5: Crear o actualizar test nodes

Para cada nodo `computation` afectado: crear al menos un nodo `test` que verifique específicamente el nuevo constraint.

### Paso 6: Validar y snapshot

Ejecutar validación. El nuevo constraint verificable se ejecutará automáticamente. Si algún nodo computation viola el nuevo constraint, el snapshot fallará — indicando exactamente qué nodos necesitan actualización de conducta.

**Nota:** Este protocolo modifica la conducta de N nodos computation tocando solo 1 nodo constraint + N edges. No se modifica ningún nodo computation en su conducta IR a menos que realmente no cumplan la regla — y en ese caso el sistema lo indica exactamente.

---

## PROTOCOLO 4 — Manejar un error de sistema

Cuando el sistema falla en producción y se detecta un error:

### Paso 1: Localizar el nodo que produce el error

El error es un evento tipado. Encontrar el nodo `event` correspondiente al error. Desde ese nodo, seguir edges `produces` entrantes para encontrar el nodo `computation` que lo emite.

### Paso 2: Cargar contexto del nodo afectado

Aplicar Protocolo 2, Paso 2.

### Paso 3: Analizar la causa

Con el nodo en contexto: revisar su conducta IR, sus constraints, y sus test nodes. Determinar:

- ¿El error es un caso no cubierto por ningún test node? → Fallo de especificación
- ¿El error viola un constraint existente? → Fallo de implementación
- ¿El error viene de un nodo dependiente con datos incorrectos? → Problema en el productor de datos

### Paso 4: Crear el test node que reproduce el bug

Antes de modificar cualquier código: crear un nodo `test` que representa exactamente la situación que causó el error. Agregar edge `tests` al nodo `computation` afectado.

Este test node debe **fallar** con el sistema actual. Si pasa, no has reproducido el bug.

### Paso 5: Aplicar Protocolo 2 para corregir la conducta

La corrección se verifica automáticamente: el nuevo test node que reproduce el bug debe pasar. Los test nodes existentes no deben fallar.

---

## PROTOCOLO 5 — Deprecar y reemplazar un nodo

Cuando un nodo debe ser reemplazado por una nueva implementación:

### Paso 1: Crear el nodo de reemplazo

Crear el nuevo nodo siguiendo el Protocolo relevante. El nuevo nodo NO hereda automáticamente los edges del antiguo.

### Paso 2: Migrar dependientes gradualmente

Para cada nodo que depende del antiguo:
1. Evaluar si la nueva firma del reemplazo es compatible
2. Si es compatible: actualizar el edge `depends-on` para apuntar al nuevo nodo
3. Si no es compatible: actualizar también el nodo dependiente (Protocolo 2)
4. Proceder nodo por nodo, validando en cada paso

### Paso 3: Deprecar el nodo antiguo

Cuando no quedan edges `depends-on` activos apuntando al nodo antiguo:
1. Agregar edge `belongs-to → deprecated` al nodo antiguo
2. El nodo antiguo aún existe en el historial (snapshots anteriores)
3. No existe en el estado activo del grafo

### Paso 4: No eliminar el historial

Los snapshots anteriores que contienen el nodo antiguo son inmutables. El nodo existió, sus versiones son accesibles. El rollback a un snapshot anterior restaurará el nodo antiguo si se restaura a ese punto en el tiempo.

---

## ANTI-PATRONES — Lo que no se hace en este paradigma

### Anti-patrón 1: "Crear archivos"

No existe la acción "crear un archivo". Existe crear nodos. La organización en archivos es una vista generada desde el grafo para consumo humano o para compiladores que requieren texto.

### Anti-patrón 2: "Buscar en el código"

No existe buscar texto en el código. Existe búsqueda semántica por embedding (para encontrar por significado) y traversal de grafo desde un nodo conocido (para navegar por relaciones). El texto del código es un artefacto de salida, no el almacenamiento primario.

### Anti-patrón 3: "Agregar un comentario para explicar"

No existen comentarios en el paradigma. Si algo necesita explicación:
- Es un concepto del dominio → crear nodo `ontology`
- Es una regla de negocio → crear nodo `constraint`
- Es una decisión de diseño con historia → agregar al intent node del snapshot
- Es un TODO → crear un issue node

Si nada de lo anterior aplica, la explicación no pertenece al sistema.

### Anti-patrón 4: "Organizar en carpetas"

No existe la organización en carpetas. La organización es declarada via edges `belongs-to` a nodos de partición, dominio, o contexto. Una IA no navega el sistema buscando en carpetas — navega por edges tipados o por búsqueda semántica.

### Anti-patrón 5: "Copiar código similar"

No existe copiar código. Si dos nodos tienen conducta similar:
- Si es idéntica: son el mismo nodo (misma ID por content-addressing)
- Si es similar pero diferente: existe un nodo más abstracto del que ambos `depend-on`, o un nodo del que ambos `derives-from` con modificación
- Si la similitud es coincidencia sin relación semántica: son nodos independientes

### Anti-patrón 6: "Agregar más contexto para entender mejor"

El contexto no se expande "para entender mejor". Se expande solo cuando una operación específica lo requiere (Regla III.4). Cargar más contexto del necesario desperdicia tokens — el recurso más crítico del paradigma.

### Anti-patrón 7: "Escribir la validación dentro de la función"

La validación no vive dentro de nodos `computation`. Vive en nodos `constraint` con edges `constrained-by`. Un nodo computation no valida sus inputs — declara los constraints que aplican a sus inputs, y el compilador inyecta la validación.

### Anti-patrón 8: "Heredar de una clase base"

La herencia no existe en este paradigma. Los mecanismos equivalentes son:
- Compartir datos: edge `depends-on` a un nodo `data` compartido
- Compartir comportamiento: edge `depends-on` a un nodo `computation` compartido
- Polimorfismo: edge `dispatches-to` a múltiples nodos con firmas compatibles
- Especialización: crear nodo nuevo con edge `derives-from` al nodo base

---

## Notas de Transición

Si se trabaja con un sistema existente escrito en el paradigma actual (código fuente en archivos), el proceso de transición es:

1. **No reescribir todo.** El grafo semántico puede coexistir con código existente.
2. **Comenzar por los constraints:** identificar las reglas de negocio implícitas en el código existente y extraerlas como nodos `constraint`. Esto ya agrega valor sin tocar la implementación.
3. **Comenzar por los boundaries:** modelar los endpoints/APIs existentes como nodos `boundary`. Esto permite generar documentación externa automáticamente.
4. **Migrar funcionalidades nueva primera:** el código nuevo se crea directamente en el grafo semántico. El código existente se deja hasta que necesite cambiar.
5. **Cuando una funcionalidad existente necesita cambio:** ese es el momento de migrarla al grafo semántico en lugar de editarla en el paradigma anterior.

La transición es incremental. El sistema es útil desde el primer nodo, no solo cuando todo está migrado.
