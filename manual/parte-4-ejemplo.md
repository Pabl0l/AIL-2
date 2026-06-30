# AIL — Manual del Paradigma
## Parte 4: El Ejemplo — Sistema de Blog

---

> El mismo sistema implementado en ambos paradigmas. La comparación final es cuantitativa.

---

## El sistema

Un blog con las siguientes capacidades:
- Autores pueden crear y editar artículos
- Los artículos pueden estar en borrador o publicados
- Los lectores pueden comentar en artículos publicados
- Los comentarios requieren moderación antes de ser visibles
- Las categorías organizan los artículos
- Solo el autor puede editar su propio artículo

---

## Paradigma actual — Node.js / TypeScript

### Estructura de archivos

```
src/
├── domain/
│   ├── entities/
│   │   ├── Article.ts
│   │   ├── Author.ts
│   │   ├── Comment.ts
│   │   └── Category.ts
│   ├── value-objects/
│   │   ├── ArticleStatus.ts
│   │   ├── CommentStatus.ts
│   │   └── Slug.ts
│   ├── repositories/
│   │   ├── IArticleRepository.ts
│   │   ├── IAuthorRepository.ts
│   │   ├── ICommentRepository.ts
│   │   └── ICategoryRepository.ts
│   └── services/
│       ├── ArticleService.ts
│       ├── CommentModerationService.ts
│       └── SlugGeneratorService.ts
├── application/
│   ├── use-cases/
│   │   ├── CreateArticle.ts
│   │   ├── PublishArticle.ts
│   │   ├── EditArticle.ts
│   │   ├── AddComment.ts
│   │   ├── ModerateComment.ts
│   │   └── GetArticlesByCategory.ts
│   ├── dtos/
│   │   ├── CreateArticleDto.ts
│   │   ├── EditArticleDto.ts
│   │   ├── AddCommentDto.ts
│   │   └── ModerateCommentDto.ts
│   └── interfaces/
│       └── IBlogApplicationService.ts
├── infrastructure/
│   ├── database/
│   │   ├── repositories/
│   │   │   ├── PostgresArticleRepository.ts
│   │   │   ├── PostgresAuthorRepository.ts
│   │   │   ├── PostgresCommentRepository.ts
│   │   │   └── PostgresCategoryRepository.ts
│   │   ├── entities/
│   │   │   ├── ArticleEntity.ts
│   │   │   ├── AuthorEntity.ts
│   │   │   ├── CommentEntity.ts
│   │   │   └── CategoryEntity.ts
│   │   └── migrations/
│   │       └── 001_initial_schema.ts
│   └── http/
│       ├── controllers/
│       │   ├── ArticleController.ts
│       │   ├── CommentController.ts
│       │   └── CategoryController.ts
│       ├── middleware/
│       │   ├── auth.middleware.ts
│       │   └── validation.middleware.ts
│       └── routes/
│           ├── article.routes.ts
│           ├── comment.routes.ts
│           └── category.routes.ts
├── shared/
│   ├── Result.ts
│   ├── DomainError.ts
│   └── BaseEntity.ts
└── tests/
    ├── unit/
    │   ├── domain/
    │   │   ├── Article.test.ts
    │   │   ├── ArticleService.test.ts
    │   │   └── CommentModerationService.test.ts
    │   └── application/
    │       ├── CreateArticle.test.ts
    │       ├── PublishArticle.test.ts
    │       └── AddComment.test.ts
    └── integration/
        ├── ArticleRepository.test.ts
        └── ArticleController.test.ts
```

**Total: 43 archivos**

### Muestra representativa de código (CreateArticle.ts)

```typescript
// src/application/use-cases/CreateArticle.ts
import { Injectable } from '@nestjs/common';
import { IArticleRepository } from '../repositories/IArticleRepository';
import { IAuthorRepository } from '../repositories/IAuthorRepository';
import { CreateArticleDto } from '../dtos/CreateArticleDto';
import { Article } from '../../domain/entities/Article';
import { ArticleStatus } from '../../domain/value-objects/ArticleStatus';
import { SlugGeneratorService } from '../../domain/services/SlugGeneratorService';
import { Result } from '../../shared/Result';
import { DomainError } from '../../shared/DomainError';

@Injectable()
export class CreateArticle {
  constructor(
    private readonly articleRepository: IArticleRepository,
    private readonly authorRepository: IAuthorRepository,
    private readonly slugGenerator: SlugGeneratorService,
  ) {}

  async execute(dto: CreateArticleDto, requesterId: string): Promise<Result<Article>> {
    // Verify author exists and matches requester
    const author = await this.authorRepository.findById(dto.authorId);
    if (!author) {
      return Result.fail(new DomainError('AUTHOR_NOT_FOUND', 'Author not found'));
    }
    if (author.userId !== requesterId) {
      return Result.fail(new DomainError('UNAUTHORIZED', 'Only the author can create their articles'));
    }

    // Generate unique slug
    const slug = await this.slugGenerator.generate(dto.title);
    const existingWithSlug = await this.articleRepository.findBySlug(slug);
    if (existingWithSlug) {
      return Result.fail(new DomainError('SLUG_CONFLICT', 'An article with this title already exists'));
    }

    // Validate title length
    if (dto.title.length < 5 || dto.title.length > 200) {
      return Result.fail(new DomainError('INVALID_TITLE', 'Title must be between 5 and 200 characters'));
    }

    // Create article
    const article = new Article({
      title: dto.title,
      content: dto.content,
      authorId: dto.authorId,
      categoryId: dto.categoryId,
      slug,
      status: ArticleStatus.DRAFT,
      createdAt: new Date(),
      updatedAt: new Date(),
    });

    await this.articleRepository.save(article);
    return Result.ok(article);
  }
}
```

### Métricas del paradigma actual

| Métrica | Valor |
|---|---|
| Archivos totales | 43 |
| Líneas de código (estimado) | ~2,800 |
| Tokens para cargar CreateArticle + contexto necesario | ~3,200–4,500 |
| Tokens para entender dónde vive "solo el autor puede editar" | ~2,000+ (distribuido en middleware, controller, use-case) |
| Archivos a tocar para agregar una regla de negocio transversal | 3–8 |
| Reglas de negocio explícitamente declaradas | 0 (están en código, comentarios, o documentación externa) |
| Documentación API mantenida manualmente | Sí |

---

## Este paradigma — Grafo semántico

### Inventario del grafo

#### Nodos ontology (conceptos del dominio)

```
on:articulo          — "Pieza de contenido autoral con título, cuerpo y estado"
on:autor             — "Persona con identidad verificada que produce artículos"
on:comentario        — "Respuesta de lector a un artículo publicado"
on:categoria         — "Agrupación temática de artículos"
on:borrador          — "Estado de artículo en preparación, no visible públicamente"
on:publicado         — "Estado de artículo visible para lectores"
on:moderacion        — "Proceso de revisión de contenido antes de publicación"
on:slug              — "Identificador URL único derivado del título"
```

#### Nodos constraint (reglas de negocio)

```
cn:solo-autor-edita
  enunciado: "Solo el autor de un artículo puede editarlo o publicarlo"
  verificable: true
  nodo_verificacion: sn:verificar-autoria

cn:articulo-publicado-para-comentar
  enunciado: "Solo se pueden agregar comentarios a artículos con estado publicado"
  verificable: true
  nodo_verificacion: sn:verificar-estado-publicado

cn:comentario-requiere-moderacion
  enunciado: "Un comentario solo es visible después de ser aprobado por moderación"
  verificable: true
  nodo_verificacion: sn:verificar-estado-moderacion

cn:slug-unico
  enunciado: "Cada artículo tiene un slug único en el sistema"
  verificable: true
  nodo_verificacion: sn:verificar-unicidad-slug

cn:titulo-valido
  enunciado: "El título de un artículo tiene entre 5 y 200 caracteres"
  verificable: true
  nodo_verificacion: sn:verificar-longitud-titulo

cn:moderador-autorizado
  enunciado: "Solo usuarios con rol moderador o admin pueden aprobar/rechazar comentarios"
  verificable: true
  nodo_verificacion: sn:verificar-rol-moderador
```

#### Nodos data (estructuras)

```
sn:articulo-data
  campos: [id, titulo, contenido, slug, estado, autor_id, categoria_id, creado_en, actualizado_en]
  edges: constrained-by → cn:titulo-valido, cn:slug-unico

sn:autor-data
  campos: [id, nombre, email, user_id, bio]

sn:comentario-data
  campos: [id, contenido, autor_id, articulo_id, estado, creado_en]

sn:categoria-data
  campos: [id, nombre, slug, descripcion]
```

#### Nodos computation (comportamiento)

```
sn:crear-articulo
  firma: (titulo, contenido, autor_id, categoria_id) → articulo | error
  depends-on: [sn:articulo-data, sn:autor-data, sn:generar-slug, sn:verificar-autoria]
  constrained-by: [cn:solo-autor-edita, cn:titulo-valido, cn:slug-unico]
  produces: [ev:articulo-creado, ev:error-autoria, ev:error-slug-duplicado, ev:error-titulo-invalido]

sn:publicar-articulo
  firma: (articulo_id, requester_id) → articulo_publicado | error
  depends-on: [sn:articulo-data, sn:verificar-autoria]
  constrained-by: [cn:solo-autor-edita]
  produces: [ev:articulo-publicado, ev:error-autoria]

sn:editar-articulo
  firma: (articulo_id, campos_a_editar, requester_id) → articulo | error
  depends-on: [sn:articulo-data, sn:verificar-autoria, sn:generar-slug]
  constrained-by: [cn:solo-autor-edita, cn:titulo-valido, cn:slug-unico]
  produces: [ev:articulo-editado, ev:error-autoria, ev:error-titulo-invalido]

sn:agregar-comentario
  firma: (contenido, autor_id, articulo_id) → comentario_pendiente | error
  depends-on: [sn:comentario-data, sn:articulo-data]
  constrained-by: [cn:articulo-publicado-para-comentar]
  produces: [ev:comentario-creado, ev:error-articulo-no-publicado]

sn:moderar-comentario
  firma: (comentario_id, decision, moderador_id) → comentario | error
  depends-on: [sn:comentario-data, sn:verificar-rol-moderador]
  constrained-by: [cn:moderador-autorizado]
  produces: [ev:comentario-aprobado, ev:comentario-rechazado, ev:error-no-autorizado]

sn:obtener-articulos-por-categoria
  firma: (categoria_id, pagina, limite) → [articulo]
  depends-on: [sn:articulo-data, sn:categoria-data]
  produces: [ev:articulos-listados]

sn:generar-slug        — genera slug único desde título
sn:verificar-autoria   — verifica que requester_id === articulo.autor_id
sn:verificar-rol-moderador  — verifica rol del usuario
```

#### Nodos event

```
ev:articulo-creado          ev:articulo-publicado       ev:articulo-editado
ev:comentario-creado        ev:comentario-aprobado      ev:comentario-rechazado
ev:error-autoria            ev:error-slug-duplicado     ev:error-titulo-invalido
ev:error-articulo-no-publicado   ev:error-no-autorizado
```

#### Nodos test (muestra)

```
tn:crear-articulo-caso-feliz
  testea: sn:crear-articulo
  dado: { titulo: "Mi primer artículo", contenido: "...", autor_id: "a1", categoria_id: "c1" }
  espera: { evento: ev:articulo-creado, articulo.estado: borrador }

tn:crear-articulo-requester-no-es-autor
  testea: sn:crear-articulo
  dado: { titulo: "Artículo", autor_id: "a1", requester_id: "a2" }
  espera: { evento: ev:error-autoria }

tn:crear-articulo-titulo-muy-corto
  testea: sn:crear-articulo
  dado: { titulo: "Hi", contenido: "...", autor_id: "a1" }
  espera: { evento: ev:error-titulo-invalido }

tn:comentar-articulo-en-borrador
  testea: sn:agregar-comentario
  dado: { articulo_id: "art-borrador", contenido: "..." }
  espera: { evento: ev:error-articulo-no-publicado }

tn:moderar-comentario-sin-permiso
  testea: sn:moderar-comentario
  dado: { comentario_id: "c1", decision: aprobado, moderador_id: "lector-sin-rol" }
  espera: { evento: ev:error-no-autorizado }
```

#### Nodos boundary (API)

```
bn:POST-articulos
  protocolo: http-rest
  external_name: "POST /articles"
  resolves-to: sn:crear-articulo
  constrained-by: [cn:requires-auth]

bn:PATCH-articulo-publicar
  protocolo: http-rest
  external_name: "PATCH /articles/{id}/publish"
  resolves-to: sn:publicar-articulo
  constrained-by: [cn:requires-auth]

bn:PATCH-articulo-editar
  protocolo: http-rest
  external_name: "PATCH /articles/{id}"
  resolves-to: sn:editar-articulo
  constrained-by: [cn:requires-auth]

bn:POST-comentario
  protocolo: http-rest
  external_name: "POST /articles/{id}/comments"
  resolves-to: sn:agregar-comentario
  constrained-by: [cn:requires-auth]

bn:PATCH-comentario-moderar
  protocolo: http-rest
  external_name: "PATCH /comments/{id}/moderate"
  resolves-to: sn:moderar-comentario
  constrained-by: [cn:requires-auth, cn:moderador-autorizado]

bn:GET-articulos-categoria
  protocolo: http-rest
  external_name: "GET /categories/{id}/articles"
  resolves-to: sn:obtener-articulos-por-categoria
```

### Inventario total del grafo

| Tipo de nodo | Cantidad |
|---|---|
| ontology | 8 |
| constraint | 6 |
| data | 4 |
| computation | 9 |
| event | 11 |
| test | 21 |
| boundary | 6 |
| **Total nodos** | **65** |

---

## Comparación cuantitativa

### Número de unidades

| Unidad | Paradigma actual | Este paradigma |
|---|---|---|
| Archivos | 43 | 0 (no existen archivos como unidad primaria) |
| Clases / interfaces | 31 | 0 |
| Funciones/métodos declarados | ~85 | 9 (nodos computation) |
| Nodos semánticos | — | 65 |

### Tokens para operaciones de edición

| Operación | Paradigma actual | Este paradigma |
|---|---|---|
| **Editar lógica de crear artículo** | ~3,200 tokens (archivo + imports + entidades + interfaces) | ~420 tokens (nodo + 6 dependencias + 2 constraints + 3 test nodes) |
| **Agregar nueva regla de negocio global** | ~2,000+ tokens (leer middleware, controller, use-case, tests) | ~80 tokens (leer/crear constraint node + agregar edges) |
| **Entender dónde está la regla "solo el autor edita"** | ~2,500 tokens (buscar en 5-8 archivos) | ~30 tokens (query: `MATCH (cn:solo-autor-edita)-[:constrained-by]-(n) RETURN n`) |
| **Agregar un endpoint nuevo** | ~1,800 tokens (controller + route + DTO + test) | ~200 tokens (boundary node + edge + 3 test nodes) |
| **Cambiar el umbral de longitud de título** | ~800 tokens (localizar la validación dispersa en use-cases) | ~40 tokens (editar valor en cn:titulo-valido) |
| **Entender qué puede fallar en una operación** | ~3,000 tokens (leer todos los try/catch de la cadena) | ~60 tokens (query edges `produces` del nodo) |

### Distribución de reglas de negocio

| Aspecto | Paradigma actual | Este paradigma |
|---|---|---|
| "Solo el autor puede editar" | En 3 archivos distintos (middleware, use-case, test) | 1 nodo constraint |
| Validación de título | Embebida en CreateArticle.ts y EditArticle.ts | 1 nodo constraint |
| Comentario requiere moderación | En lógica de AddComment + queries de listado | 1 nodo constraint |
| Estado para comentar | Verificación embebida en AddComment | 1 nodo constraint |
| **Total reglas explícitas** | **0** (implícitas en código) | **6 nodos constraint** |

### Costo de mantenimiento (escenario: "agregar rate limiting a todas las operaciones de escritura")

**Paradigma actual:**
1. Agregar middleware de rate limiting
2. Aplicarlo en routes/article.routes.ts
3. Aplicarlo en routes/comment.routes.ts
4. Actualizar tests de integración
5. Actualizar documentación API
6. Revisar que no se haya olvidado ninguna ruta
- **Archivos tocados: 5–8. Tokens de contexto: ~4,000–6,000**

**Este paradigma:**
1. Crear nodo constraint `cn:rate-limited-escritura`
2. Agregar edges `constrained-by` desde los 4 nodos computation de escritura
3. El compilador inyecta el rate limiting automáticamente
4. Los boundary nodes ya exponen la configuración actualizada en la documentación generada
- **Nodos tocados: 1 creado + 4 edges. Tokens de contexto: ~200**

---

## La diferencia no es el código — es dónde vive el conocimiento

En el paradigma actual, el conocimiento de negocio (las reglas, las invariantes, los conceptos del dominio) está **disperso en código**. Para entender qué hace el sistema, hay que leer el código. Para cambiar una regla, hay que encontrar todas sus manifestaciones.

En este paradigma, el conocimiento de negocio está **concentrado en nodos constraint y ontology**. El código (IR de nodos computation) implementa ese conocimiento. Para entender las reglas del sistema: cargar los nodos constraint. Para cambiar una regla: modificar un nodo.

Esta separación es la fuente de casi todos los beneficios cuantitativos del paradigma.

---

## Verificación: ¿qué ocurre cuando el sistema escala?

**A 10× el tamaño (sistema completo de publicación con 50 operaciones):**

| Métrica | Paradigma actual × 10 | Este paradigma × 10 |
|---|---|---|
| Archivos | ~430 | 0 archivos |
| Tokens para editar una función | ~5,000–15,000 | ~400–800 |
| Tokens para entender todas las reglas | >50,000 (leer todo el código) | ~1,800 (cargar 60 nodos constraint) |
| Tokens para agregar regla transversal | ~10,000+ | ~300 |

La diferencia entre paradigmas crece con el tamaño del sistema. El paradigma actual escala el contexto necesario linealmente con el tamaño del sistema. Este paradigma escala el contexto necesario con el tamaño de la operación local, que se mantiene constante.
