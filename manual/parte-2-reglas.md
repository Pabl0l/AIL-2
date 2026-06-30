# AIL — Manual del Paradigma
## Parte 2: Las Reglas

---

> Las reglas son prescripciones, no sugerencias. Cada una responde exactamente una pregunta que surge durante trabajo real. Cada una tiene una razón fundada en necesidad computacional.

---

## SECCIÓN I — Reglas de Identidad

*Pregunta que responde: ¿cómo identifico cualquier cosa en el sistema?*

---

### REGLA I.1 — La identidad es contenido, nunca nombre

La ID de todo nodo se deriva de su contenido mediante hash determinístico:

```
ID = "sn:" + sha256(
  tipo_de_nodo
  + serialización_canónica(firma)
  + hash_de_conducta_IR          # solo computation
  + sorted(IDs_dependencias_directas)
)
```

**Consecuencia directa:** Dos nodos con contenido idéntico tienen la misma ID. Son el mismo nodo. No pueden existir dos instancias del mismo nodo — la deduplicación es estructural, no una política.

**Anti-patrón:** Asignar IDs secuenciales, UUIDs aleatorios, o cualquier otro sistema que no depende del contenido. Eso rompe el content-addressing y permite que nodos con el mismo significado tengan identidades distintas.

---

### REGLA I.2 — Los nombres humanos son aliases, nunca identidad

Los nombres (`createPayment`, `PaymentService`, `POST /payments`, `InventoryItem`) son aliases — metadatos opcionales almacenados en la tabla de aliases, separada del nodo.

Un nodo puede tener:
- **Cero aliases:** es un nodo interno, nadie lo referencia por nombre
- **Un alias:** nombre canónico
- **Múltiples aliases:** API pública con versionado, nombres en varios idiomas, nombres históricos

Los aliases se usan exclusivamente para:
- Generar código fuente legible para inspección humana
- Nombrar endpoints externos en nodos boundary
- Buscar cuando el humano escribe un nombre como punto de entrada

Los aliases **no se usan** para navegación interna, resolución de dependencias, ni búsqueda semántica.

---

### REGLA I.3 — Renombrar es una operación de metadata

Cambiar el nombre de cualquier nodo modifica únicamente la tabla de aliases. No toca el nodo. No cambia su ID. No requiere actualizar ningún edge. No produce un nuevo snapshot por sí solo.

Renombrar un nodo es operacionalmente equivalente a renombrar un archivo en un sistema de archivos content-addressed: el contenido no cambió, solo el puntero humano.

**Consecuencia:** El "costo de renombrar" en este paradigma es O(1). En el paradigma actual es O(n) donde n es el número de referencias en el código.

---

### REGLA I.4 — Cambiar una dependencia cambia la identidad

La ID de un nodo A incluye las IDs de sus dependencias directas (sorted). Si el nodo B cambia (nueva ID), y A depende de B, entonces la ID de A también cambia cuando A actualiza su referencia a la nueva versión de B.

Esto hace que el "dependency drift" sea estructuralmente imposible: no puedes tener un nodo que dice depender de B pero en realidad usa una versión desactualizada de B sin que el sistema lo detecte. La incompatibilidad se manifiesta como una ID inválida.

---

### REGLA I.5 — La búsqueda de identidad tiene tres mecanismos, en orden

1. **Hash directo:** `graph.get("sn:a4f2e9b7")` — O(1), cuando conoces la ID
2. **Traversal de grafo:** desde un nodo conocido, seguir edges tipados — cuando conoces el contexto
3. **Búsqueda semántica:** similitud de embedding — cuando conoces el significado pero no la ubicación

Nunca búsqueda de texto (grep, regex sobre código fuente). Nunca búsqueda por nombre de archivo. El nombre de archivo no existe en este paradigma.

---

## SECCIÓN II — Reglas de Representación

*Pregunta que responde: ¿cómo expreso cualquier artefacto de software?*

---

### REGLA II.1 — Todo artefacto mapea a exactamente un tipo de nodo

Antes de crear cualquier nodo, determinar su tipo:

| Si el artefacto... | Tipo de nodo |
|---|---|
| Ejecuta lógica y produce un resultado | `computation` |
| Define la estructura de datos (campos y tipos) | `data` |
| Expresa una regla que otros deben cumplir | `constraint` |
| Representa una ocurrencia que puede suceder | `event` |
| Verifica el comportamiento de otro nodo | `test` |
| Es el punto de entrada/salida del sistema | `boundary` |
| Define un concepto del dominio de negocio | `ontology` |

Si un artefacto parece requerir dos tipos simultáneamente: no es un nodo, son dos nodos. Dividir.

---

### REGLA II.2 — El comportamiento vive en IR, nunca en texto fuente

El código fuente (TypeScript, Python, Rust, Go, etc.) es un **artefacto transitorio de síntesis**. El flujo es:

```
Especificación semántica
    → Generación de código fuente (transitorio)
    → Compilación a IR (WASM, LLVM IR)
    → Descarte del código fuente
    → Almacenamiento permanente del IR
```

El código fuente puede regenerarse desde el IR en cualquier momento para inspección humana. El IR es la verdad. El código fuente es una vista.

**Por qué IR y no código fuente:**
- El IR es estructuralmente tipado: no hay ambigüedad sintáctica
- El IR es más compacto: no contiene ceremony sintáctica
- El IR es target-agnostic: el mismo IR compila a nativo, WASM, o container
- El IR no requiere parsing: la IA trabaja directamente en estructura, no en texto

---

### REGLA II.3 — Los datos son esquemas tipados, sin métodos

Un nodo `data` define únicamente estructura: campos y sus tipos. No tiene métodos. No tiene constructor. No tiene getters/setters. No tiene lógica de validación embebida (eso pertenece a nodos `constraint`).

```
NODO data {
  tipo: data
  firma: {
    campos: [
      { nombre: "sku",           tipo: String,    restricciones: [único] },
      { nombre: "precio",        tipo: Money,     restricciones: [positivo] },
      { nombre: "punto_reorden", tipo: Cantidad,  restricciones: [min:0] }
    ]
  }
}
```

La validación de campos no vive en el nodo `data`. Vive en nodos `constraint` conectados al nodo `data` via edges `constrained-by`, o en nodos `computation` que procesan ese tipo de dato.

---

### REGLA II.4 — Las concerns transversales son edges, nunca código embebido

Autenticación, autorización, logging, rate limiting, caché, tracing, auditoría: ninguno de estos pertenece dentro de un nodo `computation`. Son concerns transversales.

**Cómo se representan:**
1. Existe un nodo `constraint` para cada concern: `cn:requires-auth`, `cn:rate-limited-100rpm`, `cn:audit-trail`
2. El nodo `computation` que requiere ese concern tiene un edge `constrained-by` al nodo constraint
3. Durante compilación, el compilador lee los edges `constrained-by` e inyecta el concern automáticamente

```
NODO computation "crear-movimiento-stock" {
  ...
  edges_salientes: [
    constrained-by → cn:requires-auth
    constrained-by → cn:rate-limited-100rpm
    constrained-by → cn:stock-no-negativo
  ]
}
```

El nodo `computation` no tiene código de autenticación. El compilador sabe que debe insertarlo.

**Por qué:** Si la autenticación vive en código embebido, modificar la política de auth requiere tocar N nodos computation. Si vive en un nodo constraint con edges, modificar la política requiere tocar un nodo.

---

### REGLA II.5 — Las relaciones son edges explícitos, sin excepción

No existen dependencias implícitas. Las siguientes formas de dependencia implícita no existen en este paradigma:

- Dependencia por nombre (convención `UserService` depende de `UserRepository`)
- Dependencia por proximidad (dos funciones en el mismo archivo)
- Dependencia por herencia implícita
- Dependencia por convención de carpeta (`infrastructure/` puede importar de `domain/`)
- Dependencia por posición en la cadena de middleware

Si A usa B: existe un edge `depends-on` de A a B. Si el edge no existe: A no puede usar B. Esta invariante se verifica en cada snapshot.

---

### REGLA II.6 — Los errores son nodos event, nunca excepciones en el flujo

Los errores no interrumpen el flujo de un nodo `computation` con excepciones. Un nodo computation que puede fallar:

1. Declara un edge `produces` a un nodo `event` de subtipo error
2. En su conducta IR, emite ese evento en las condiciones de error
3. No tiene try/catch dentro de su lógica

Los manejadores de error son nodos `computation` separados con edges `consumes` a los eventos de error correspondientes.

```
NODO computation "transferir-fondos" {
  ...
  edges_salientes: [
    produces → ev:fondos-insuficientes
    produces → ev:transferencia-exitosa
    produces → ev:cuenta-bloqueada
  ]
}

NODO computation "manejar-fondos-insuficientes" {
  ...
  edges_entrantes: [
    consumes ← ev:fondos-insuficientes
  ]
}
```

**Por qué:** La lógica de manejo de error es separable de la lógica de computación. Al separarlos en nodos distintos, cada uno puede evolucionar, probarse y reemplazarse independientemente.

---

## SECCIÓN III — Reglas de Contexto

*Pregunta que responde: ¿cuánto necesito cargar para realizar cualquier operación?*

---

### REGLA III.1 — Contexto mínimo para cualquier edición local

Para editar el nodo X, cargar exactamente:

| Qué cargar | Por qué |
|---|---|
| El nodo X | El objeto de la edición |
| Nodos en edges `depends-on` salientes de X (profundidad 1) | Lo que X necesita — sus dependencias directas |
| Nodos en edges `constrained-by` de X | Reglas que X debe cumplir después de la edición |
| Nodos `test` con edge `tests` entrante a X | Comportamiento esperado que la edición no debe romper |
| Nodos con edge `depends-on` entrante a X | Lo que depende de X — lo que no debe romperse |

**Total típico: 5–20 nodos. Máximo absoluto para edición local: 50 nodos.**

Si se necesitan más de 50 nodos para una edición local, la operación no es una edición local — es una refactorización que debe dividirse.

---

### REGLA III.2 — Profundidad máxima 2

Ninguna edición local carga el grafo a más de 2 niveles de profundidad desde el nodo objetivo.

- **Profundidad 1:** dependencias directas y dependientes directos
- **Profundidad 2:** solo cuando un fallo de tipos requiere cargar el nodo que define el tipo, o cuando un constraint requiere su nodo de verificación

**Profundidad 3+ nunca se carga automáticamente.** Si se necesita profundidad 3, la operación tiene un problema de diseño de grafo (la edit locality no está garantizada) y debe resolverse antes de proceder.

---

### REGLA III.3 — El conocimiento base está siempre en contexto

Al inicio de cualquier sesión de trabajo sobre un sistema, cargar y anclar:

1. Todos los nodos `ontology` del dominio relevante
2. Todos los nodos `constraint` del proyecto
3. Los nodos `data` de las estructuras más usadas

Estos nodos son el **conocimiento base** — nunca se expulsan del contexto durante la sesión. Su costo es fijo (una vez por sesión), no variable (una vez por operación).

**Por qué:** Una IA que necesita cargar la definición del concepto "punto de reorden" en cada operación de inventario desperdicia tokens. Cargarlo una vez al inicio y anclarlo cuesta igual que cargarlo una vez.

---

### REGLA III.4 — La expansión de contexto tiene causa explícita

El contexto solo se expande (más allá del mínimo de la Regla III.1) cuando:

1. Un fallo de compatibilidad de tipos requiere cargar el nodo que define el tipo
2. Un nodo `constraint` con `verificable: true` requiere cargar su nodo de verificación
3. Un nodo `test` falla y el diagnóstico requiere cargar dependencias transitivas

**No se expande el contexto:**
- Por precaución ("podría necesitarlo")
- Para "entender mejor el sistema antes de editar"
- Para leer documentación o comentarios

Si la IA necesita contexto adicional más allá de lo permitido para entender qué hacer, la especificación de la tarea es insuficiente y debe ser aclarada antes de proceder.

---

### REGLA III.5 — La búsqueda semántica reemplaza la expansión de contexto

Cuando la IA necesita encontrar un nodo relacionado pero no sabe su ID:

**Opción A (incorrecta):** Cargar nodos adyacentes hasta encontrarlo. Costo: O(N) nodos.

**Opción B (correcta):** Ejecutar búsqueda semántica por embedding del concepto buscado. Costo: O(1) operación + ~10 tokens de resultado.

La búsqueda semántica retorna IDs de nodos. Con la ID, el nodo se recupera en O(1). El contexto no creció explorando el grafo.

---

## SECCIÓN IV — Reglas de Cambio

*Pregunta que responde: ¿cómo modifico algo sin romper nada?*

---

### REGLA IV.1 — Los nodos son inmutables

Un nodo no se modifica in-place. Cuando un nodo necesita cambiar:

1. Se crea un nuevo nodo con el contenido modificado
2. El nuevo nodo tiene una nueva ID (diferente contenido → diferente hash)
3. El nuevo nodo tiene un edge `derives-from` al nodo anterior
4. Los edges que apuntaban al nodo anterior se actualizan explícitamente (ver Regla IV.3)

El nodo anterior no desaparece inmediatamente. Persiste en el grafo. Es accesible por su ID. Solo deja de ser parte del "estado actual" cuando ningún edge del snapshot actual lo referencia.

---

### REGLA IV.2 — Todo cambio requiere snapshot previo

Antes de modificar cualquier nodo o edge: crear un snapshot del estado actual.

El snapshot es el punto de restauración. Sin snapshot previo, no existe rollback posible.

El snapshot puede abarcar múltiples cambios relacionados (equivalente a un commit que agrupa cambios de una feature). Pero debe existir antes de que ocurra cualquier cambio.

---

### REGLA IV.3 — Las dependencias se actualizan explícitamente

Cuando el nodo B cambia (nueva versión B' con nueva ID), los nodos que tienen edge `depends-on` a B tienen exactamente tres opciones:

**Opción 1 — Adoptar la nueva versión:**
Actualizar el edge `depends-on` de B → B'. Esto cambia la propia ID del nodo dependiente (por la Regla I.4). Requiere crear una nueva versión del nodo dependiente.

**Opción 2 — Mantener la versión anterior:**
No actualizar el edge. El nodo dependiente sigue usando B (versión anterior). Esto es válido y explícito — no un descuido.

**Opción 3 — Declarar incompatibilidad:**
El cambio en B rompe la firma que el nodo dependiente espera. Esto se detecta automáticamente: la firma de B' es incompatible con lo que el edge `depends-on` del nodo dependiente requiere. Es un error de snapshot que debe resolverse.

No existe la Opción 0: "el cambio se propaga automáticamente". La propagación automática esconde decisiones.

---

### REGLA IV.4 — El refactor es transformación de grafo

Toda operación de refactorización corresponde a una transformación de grafo bien definida:

| Refactorización | Operación de grafo |
|---|---|
| **Extraer función** | Crear nodo `computation` nuevo. Redirigir edges de comportamiento compartido hacia el nuevo nodo. Agregar edge `depends-on` desde los nodos originales. |
| **Inlinar función** | Fusionar la conducta IR del nodo inline en el nodo llamante. Eliminar edge `depends-on`. Redirigir edges `tests` y `constrained-by`. |
| **Mover entre contextos** | Actualizar edges `belongs-to`. No tocar el nodo. La ID no cambia. |
| **Extraer abstracción** | Crear nodo compartido con firma generalizada. Reemplazar los N nodos duplicados con edges `depends-on` al nodo compartido. Los N nodos originales pueden eliminarse si sus edges se redistribuyen. |
| **Agregar concern transversal** | Crear nodo `constraint`. Agregar edges `constrained-by` desde los nodos afectados. No tocar la conducta de ningún nodo computation. |
| **Cambiar firma de función** | Crear nuevo nodo computation con firma modificada. Actualizar todos los edges `depends-on` entrantes que sean afectados (opción 1, 2 o 3 de la Regla IV.3). |

En ningún caso el refactor es búsqueda y reemplazo de texto. Es siempre una operación declarativa sobre la estructura del grafo.

---

### REGLA IV.5 — La eliminación es consecuencia, no acción directa

Un nodo se elimina del estado actual cuando sus edges son redirigidos o eliminados. No existe una operación "eliminar nodo X directamente".

El proceso:
1. Identificar todos los edges que apuntan a X
2. Para cada edge: actualizar el edge para apuntar a otro nodo, o eliminar el edge si la dependencia ya no existe
3. Cuando X queda sin edges entrantes en el snapshot actual, X ya no es parte del estado activo

X sigue existiendo en el historial (snapshots anteriores donde sí tenía edges). No se borra del grafo de historia.

---

## SECCIÓN V — Reglas de Conocimiento

*Pregunta que responde: ¿dónde viven las reglas de negocio y los conceptos del dominio?*

---

### REGLA V.1 — Una regla de negocio = un nodo constraint

Cada regla de negocio tiene exactamente un nodo `constraint`. La misma regla nunca se repite en múltiples lugares. Se aplica a múltiples nodos via múltiples edges `constrained-by`, pero existe una sola vez en el grafo.

```
NODO constraint "stock-no-negativo" {
  dominio: inventario
  enunciado: "El nivel de stock resultante de cualquier operación no puede ser negativo"
  severidad: error
  verificable: true
  nodo_verificacion: sn:verificar-stock-positivo
  aliases: ["stock-non-negative"]
}

edges_salientes: [
  constrained-by ← sn:crear-movimiento-salida
  constrained-by ← sn:ajustar-inventario
  constrained-by ← sn:transferir-entre-almacenes
]
```

**Lo que no existe:** La misma regla escrita como comentario en 8 funciones diferentes. Si la regla cambia, se cambia un nodo. No 8 lugares.

---

### REGLA V.2 — El dominio se define antes que la implementación

El orden correcto de creación de nodos:

```
1. Nodos ontology   → conceptos del dominio
2. Nodos constraint → reglas del dominio
3. Nodos data       → estructuras de datos
4. Nodos computation → comportamiento
5. Nodos test       → verificación
6. Nodos boundary   → exposición externa
```

Los nodos `computation` son la capa más superficial. No son el punto de partida.

**Por qué:** Un sistema cuya implementación precede al modelo de dominio acumula conceptos implícitos en el código que luego son difíciles de identificar, refactorizar o verificar. Cuando el dominio está explícito en nodos `ontology`, toda la implementación puede verificarse contra él.

---

### REGLA V.3 — Todo concepto de negocio es un nodo ontology

Antes de crear un nodo `data` o `computation` que trabaja con un concepto de negocio, verificar si existe un nodo `ontology` para ese concepto. Si no existe, crearlo.

```
NODO ontology "punto-de-reorden" {
  dominio: inventario
  definición: "Nivel mínimo de stock por debajo del cual se genera automáticamente una orden de compra"
  relacionado-con: [
    belongs-to → on:nivel-stock,
    belongs-to → on:orden-compra,
    belongs-to → on:sku
  ]
}
```

Un nodo `data` para Producto tiene un edge `belongs-to → on:punto-de-reorden`. Esto conecta la implementación al modelo de dominio. Una IA editando el nodo Producto puede cargar el concepto del dominio en contexto y entender las implicaciones sin leer documentación.

---

### REGLA V.4 — Los constraints verificables siempre tienen nodo de verificación

Un nodo `constraint` con `verificable: true` debe tener un nodo `computation` de verificación. La verificación se ejecuta automáticamente en cada snapshot.

Si un constraint no puede verificarse automáticamente, `verificable: false` — y es documentación estructurada, no una garantía ejecutable.

**La diferencia importa:** Un sistema con 50 constraints verificables y verificación automática en cada snapshot es cualitativamente diferente a un sistema donde "las reglas están en los comentarios". El primero puede garantizar corrección. El segundo solo puede aspirar a ella.

---

### REGLA V.5 — Los constraints definen el "por qué"; la conducta define el "cómo"

Separación estricta:
- **Constraint:** "El monto de transferencia no puede exceder el saldo disponible" (la regla)
- **Computation:** Lógica que ejecuta la transferencia verificando el saldo (la implementación)

El constraint existe independientemente de la implementación. Si la implementación cambia, el constraint no cambia. Si el constraint cambia (nueva regulación), se modifica el nodo constraint — la implementación puede no necesitar tocar.

---

## SECCIÓN VI — Reglas de Corrección

*Pregunta que responde: ¿cómo sé que el sistema hace lo que debe hacer?*

---

### REGLA VI.1 — Todo nodo computation tiene al menos un nodo test

Sin excepción. Un nodo `computation` sin ningún nodo `test` apuntando a él (via edge `tests`) no puede incluirse en un snapshot con estado "deployable".

Un snapshot con nodos computation sin test puede existir como estado "en desarrollo" pero no como estado que puede compilarse y desplegarse.

---

### REGLA VI.2 — Los tests son datos declarativos

Un nodo `test` es una especificación de comportamiento esperado, no código de prueba:

```
NODO test "transferir-fondos-insuficientes" {
  testea: sn:transferir-fondos
  dado: {
    cuenta_origen: { saldo: 100.00, moneda: "USD" },
    monto_transferencia: 150.00
  }
  espera: {
    evento_producido: ev:fondos-insuficientes,
    payload: { disponible: 100.00, requerido: 150.00 }
  }
}
```

No contiene imports. No contiene assertions en código. No tiene setup/teardown. Es un triplete: **dado → acción → espera**. El runner de tests sabe cómo ejecutarlo porque el tipo del nodo `test` define el protocolo.

---

### REGLA VI.3 — Los test nodes cubren casos específicos

Para cada nodo `computation`, los test nodes deben cubrir:

1. **Caso feliz (golden path):** inputs válidos, comportamiento esperado
2. **Casos límite:** valores mínimos, máximos, vacíos, nulos donde aplique
3. **Casos de error:** inputs que deben producir eventos de error
4. **Casos de constraint:** verificar que los constraints `constrained-by` se cumplen

El número mínimo de test nodes por computation node: **3** (uno por categoría 1, uno por categoría 3, uno libre).

---

### REGLA VI.4 — La cobertura es una propiedad del grafo, no del código

```
Cobertura = |nodos computation con ≥1 edge "tests" entrante| / |total nodos computation|
```

Se calcula con una consulta de grafo. No requiere ejecutar ningún test. No requiere analizar cobertura de líneas.

Umbral mínimo para snapshot deployable: **80%**.

---

### REGLA VI.5 — La consistencia de tipos es compatibilidad de edges

La verificación de tipos no es análisis de texto. Es: para cada edge `depends-on` de A → B, el tipo del output de B es compatible con el tipo del input que A declara en su firma?

Esta es una consulta de grafo sobre los metadatos de tipo en los nodos. Se ejecuta en cada snapshot. Un snapshot con edges de tipo incompatible es inválido y no puede compilarse.

---

### REGLA VI.6 — Los constraints verificables se ejecutan en cada snapshot

Todos los nodos `constraint` con `verificable: true` se ejecutan automáticamente como parte de la validación de snapshot. Un constraint verificable que falla invalida el snapshot.

El orden de verificación:
1. Consistencia de tipos (edges)
2. Constraints verificables
3. Tests (coverage)
4. Security scan (edges de boundary sin auth constraint)

Un snapshot solo tiene estado "valid" cuando pasa todos los niveles.

---

## SECCIÓN VII — Reglas de Tiempo

*Pregunta que responde: ¿cómo evolucionan el sistema y su historia?*

---

### REGLA VII.1 — La unidad de versión es el snapshot

Un snapshot es un estado consistente e inmutable del grafo completo. Tiene:

```
SNAPSHOT {
  id:          hash del estado completo del grafo
  padre:       ID del snapshot anterior
  delta: {
    nodos_agregados:    [lista de IDs]
    nodos_eliminados:   [lista de IDs]
    nodos_modificados:  [{ anterior: ID, posterior: ID }]
    edges_agregados:    [lista de (source, tipo, target)]
    edges_eliminados:   [lista de (source, tipo, target)]
  }
  hash_grafo:  sha256 del estado completo
  timestamp:   ISO-8601
  intención:   referencia al intent node que motivó estos cambios
  estado:      "en_desarrollo" | "valid" | "deployable"
}
```

---

### REGLA VII.2 — No existen diffs de texto

El diff entre dos snapshots es semántico. Se calcula como la diferencia entre los conjuntos de nodos y edges de cada snapshot:

- Qué nodos se agregaron
- Qué nodos se modificaron (IDs anterior y posterior)
- Qué nodos se eliminaron
- Qué edges cambiaron

El diff de texto (mostrando líneas de código modificadas) es un artefacto generado opcionalmente para consumo humano. No es el almacenamiento primario.

**Por qué importa:** Un diff semántico dice "se modificó el constraint de validación de stock y se agregaron 3 test nodes". Un diff de texto dice "se cambiaron 47 líneas en 8 archivos". El primero tiene significado. El segundo requiere interpretación.

---

### REGLA VII.3 — El rollback es restauración de snapshot

Volver a cualquier versión anterior del sistema significa: cargar el snapshot anterior como estado actual. No hay "revert de commits individuales". El sistema regresa exactamente al estado del snapshot elegido — incluyendo todos sus nodos y edges.

El estado actual siempre es el snapshot más reciente con estado "deployable" (o el snapshot de trabajo actual si se está en medio de cambios).

---

### REGLA VII.4 — El historial de un nodo es una cadena de edges `derives-from`

Para reconstruir la historia de evolución de cualquier nodo: traversal de edges `derives-from` hacia atrás, siguiendo la cadena de versiones.

```
sn:transferir-fondos:v4
  derives-from → sn:transferir-fondos:v3    (snapshot:00089)
    derives-from → sn:transferir-fondos:v2  (snapshot:00045)
      derives-from → sn:transferir-fondos:v1 (snapshot:00012)
```

Cada nodo en la cadena tiene su snapshot de referencia. El snapshot tiene el intent node que motivó el cambio. La historia completa de decisiones es reconstruible.

---

### REGLA VII.5 — El trabajo paralelo opera sobre particiones

Múltiples agentes pueden modificar el grafo simultáneamente si operan sobre particiones distintas. Un conflicto real (dos agentes modificando el mismo nodo a partir del mismo estado base) se detecta cuando ambos producen nuevos nodos con el mismo `derives-from` pero diferente ID.

La resolución de conflicto es semántica: ¿cuál versión del nodo satisface mejor los constraints vigentes? ¿Son las versiones reconciliables (sus cambios son en partes distintas de la conducta)? Esta evaluación la hace el agente orquestador, no un merge automático de texto.

---

## Resumen de las Reglas

**Identidad:** Los nodos son lo que son. No lo que se llaman.

**Representación:** Todo tiene un tipo. Todo tiene un lugar. Nada está embebido donde no pertenece.

**Contexto:** Cargar lo mínimo necesario. Anclar lo que siempre se necesita. Buscar semánticamente antes de expandir.

**Cambio:** Los nodos no mutan. Las decisiones son explícitas. El refactor es transformación de grafo.

**Conocimiento:** El dominio precede a la implementación. Las reglas son nodos, no prosa.

**Corrección:** Todo computation tiene tests. Los constraints se verifican automáticamente. Los tipos son edges, no texto.

**Tiempo:** La historia es una cadena de snapshots semánticos. El rollback es restauración. El diff es significado, no líneas.
