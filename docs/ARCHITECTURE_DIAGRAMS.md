# Architecture Diagrams

Visual diagrams for understanding the Wagtail Context Search architecture.

## Query Processing Flow

```mermaid
graph TD
    A[User Types Query] --> B[Frontend Widget]
    B -->|POST /rag/query/| C[Django View: query_view]
    C -->|Initialize| D[RAGRetrieval]
    C -->|Initialize| E[RAGGenerator]
    
    D -->|1. Embed Query| F[Embedder Backend]
    F -->|query_embedding| D
    
    D -->|2. Search| G{Vector DB Backend}
    G -->|ChromaDB| H[ChromaDB<br/>Vector Search]
    G -->|Meilisearch| I[Meilisearch<br/>Full-Text Search]
    G -->|PGVector| J[PostgreSQL<br/>pgvector]
    G -->|Qdrant| K[Qdrant<br/>Vector Search]
    
    H -->|documents[]| D
    I -->|documents[]| D
    J -->|documents[]| D
    K -->|documents[]| D
    
    D -->|documents[]| C
    C -->|query + documents| E
    
    E -->|3. Build Prompt| L[Prompt Template]
    L -->|formatted_prompt| E
    
    E -->|4. Generate Answer| M{LLM Backend}
    M -->|OpenAI| N[GPT Models]
    M -->|Anthropic| O[Claude Models]
    M -->|Ollama| P[Local LLM]
    
    N -->|answer| E
    O -->|answer| E
    P -->|answer| E
    
    E -->|answer + sources| C
    C -->|JSON Response| B
    B -->|Display| A
    
    style A fill:#e1f5ff
    style B fill:#fff4e1
    style C fill:#ffe1f5
    style D fill:#e1ffe1
    style E fill:#ffe1e1
    style F fill:#f0e1ff
    style G fill:#ffffe1
    style M fill:#ffffe1
```

## System Components

```mermaid
graph LR
    subgraph "Frontend Layer"
        A[Chat Widget<br/>JavaScript]
        B[CSS Styles]
        C[Template Tag]
    end
    
    subgraph "Django Layer"
        D[URLs]
        E[Views]
        F[Models]
        G[Signals]
    end
    
    subgraph "Core Layer"
        H[RAGRetrieval]
        I[RAGGenerator]
        J[Prompt Templates]
        K[Text Chunker]
    end
    
    subgraph "Backend Layer - LLM"
        L1[OpenAI]
        L2[Anthropic]
        L3[Ollama]
    end
    
    subgraph "Backend Layer - Embedder"
        E1[OpenAI Embeddings]
        E2[Sentence Transformers]
    end
    
    subgraph "Backend Layer - Vector DB"
        V1[ChromaDB]
        V2[Meilisearch]
        V3[PostgreSQL/pgvector]
        V4[Qdrant]
    end
    
    A --> D
    C --> A
    D --> E
    E --> H
    E --> I
    H --> E1
    H --> E2
    H --> V1
    H --> V2
    H --> V3
    H --> V4
    I --> J
    I --> L1
    I --> L2
    I --> L3
    G --> F
    G --> H
    H --> K
    
    style A fill:#e1f5ff
    style E fill:#ffe1f5
    style H fill:#e1ffe1
    style I fill:#ffe1e1
```

## Indexing Flow

```mermaid
sequenceDiagram
    participant W as Wagtail CMS
    participant S as Signal Handler
    participant C as Content Extractor
    participant Ch as Chunker
    participant E as Embedder
    participant V as Vector DB
    participant D as Django DB
    
    W->>S: Page Published
    S->>C: Extract Content
    C->>C: Get Page Text
    C-->>S: content_text
    
    S->>Ch: chunk_text(content)
    Ch-->>S: chunks[]
    
    S->>E: embed_batch(chunks)
    E-->>S: embeddings[]
    
    loop For each chunk
        S->>V: add_documents(doc, embedding)
        V-->>S: success
    end
    
    S->>D: IndexedPage.save()
    D-->>S: saved
    
    Note over W,D: Page is now searchable
```

## Data Model

```mermaid
erDiagram
    Page ||--o| IndexedPage : "has"
    IndexedPage ||--o{ ChunkMetadata : "has"
    
    Page {
        int id PK
        string title
        string slug
        datetime first_published_at
        datetime last_published_at
        bool live
    }
    
    IndexedPage {
        int page_id PK_FK
        string page_type
        string title
        url url
        datetime last_indexed
        datetime last_modified
        int chunk_count
        bool is_active
    }
    
    ChunkMetadata {
        int id PK
        int page_id FK
        string chunk_id
        int chunk_index
        text chunk_text
    }
    
    VectorDB {
        string chunk_id PK
        vector embedding
        text text
        json metadata
    }
```

## Backend Selection

```mermaid
graph TD
    A[Configuration<br/>WAGTAIL_CONTEXT_SEARCH] -->|LLM_BACKEND| B{LLM Selection}
    A -->|EMBEDDER_BACKEND| C{Embedder Selection}
    A -->|VECTOR_DB_BACKEND| D{Vector DB Selection}
    
    B -->|openai| E[OpenAIBackend]
    B -->|anthropic| F[AnthropicBackend]
    B -->|ollama| G[OllamaBackend]
    
    C -->|openai| H[OpenAIEmbedder]
    C -->|sentence_transformers| I[SentenceTransformersEmbedder]
    
    D -->|chroma| J[ChromaBackend]
    D -->|meilisearch| K[MeilisearchBackend]
    D -->|pgvector| L[PGVectorBackend]
    D -->|qdrant| M[QdrantBackend]
    
    E --> N[Initialized System]
    F --> N
    G --> N
    H --> N
    I --> N
    J --> N
    K --> N
    L --> N
    M --> N
    
    style A fill:#ffe1f5
    style N fill:#e1ffe1
```

## Complete System Architecture

```mermaid
graph TB
    subgraph "User Interaction"
        U[User]
        UI[Browser UI]
    end
    
    subgraph "Wagtail Site"
        WS[Wagtail CMS]
        PG[Pages]
    end
    
    subgraph "Wagtail Context Search Plugin"
        subgraph "Frontend"
            WT[Widget Template]
            JS[JavaScript]
            CSS[Styles]
        end
        
        subgraph "Django App"
            URL[URL Router]
            VW[Views]
            MD[Models]
            SG[Signals]
            MT[Management Commands]
        end
        
        subgraph "Core Engine"
            RT[RAGRetrieval]
            GN[RAGGenerator]
            CH[Chunker]
            PT[Prompt Templates]
        end
        
        subgraph "Backends"
            LLM[LLM Backends]
            EMB[Embedder Backends]
            VDB[Vector DB Backends]
        end
    end
    
    subgraph "External Services"
        OAI[OpenAI API]
        ANT[Anthropic API]
        OLL[Ollama Server]
        CHR[ChromaDB]
        MEI[Meilisearch]
        PGDB[(PostgreSQL)]
        QDR[Qdrant]
    end
    
    U --> UI
    UI --> WT
    WT --> JS
    JS -->|HTTP POST| URL
    URL --> VW
    VW --> RT
    VW --> GN
    
    RT --> EMB
    RT --> VDB
    GN --> LLM
    
    EMB --> OAI
    EMB --> OLL
    LLM --> OAI
    LLM --> ANT
    LLM --> OLL
    VDB --> CHR
    VDB --> MEI
    VDB --> PGDB
    VDB --> QDR
    
    WS --> PG
    PG -->|Signals| SG
    SG --> RT
    SG --> MD
    MT --> RT
    
    GN -->|Response| VW
    VW -->|JSON| JS
    JS --> UI
    UI --> U
    
    style U fill:#e1f5ff
    style RT fill:#e1ffe1
    style GN fill:#ffe1e1
    style LLM fill:#ffffe1
    style EMB fill:#ffffe1
    style VDB fill:#ffffe1
```

## Query Processing States

```mermaid
stateDiagram-v2
    [*] --> Idle: System Ready
    
    Idle --> Receiving: User Submits Query
    Receiving --> Validating: POST Request Received
    
    Validating --> Retrieving: Query Valid
    Validating --> Error: Invalid Query
    
    Retrieving --> Embedding: Initialize Retrieval
    Embedding --> Searching: Query Embedded
    Searching --> Retrieved: Documents Found
    
    Retrieved --> Generating: Initialize Generator
    Generating --> Prompting: Build Prompt
    Prompting --> LLMQuery: Send to LLM
    LLMQuery --> LLMResponse: LLM Processing
    LLMResponse --> Formatting: Answer Received
    
    Formatting --> Responding: Format Response
    Responding --> [*]: JSON Response Sent
    
    Error --> [*]: Error Response Sent
    Retrieved --> Error: No Documents Found
    LLMResponse --> Error: LLM Failed
```

## Error Handling Flow

```mermaid
graph TD
    A[Request Received] --> B{Valid Query?}
    B -->|No| C[Return 400 Error]
    B -->|Yes| D{LLM Available?}
    D -->|No| E[Return 503 Error]
    D -->|Yes| F{Embedder Available?}
    F -->|No| G[Return 500 Error]
    F -->|Yes| H{Vector DB Available?}
    H -->|No| I[Return 500 Error]
    H -->|Yes| J[Process Query]
    
    J --> K{Retrieval Success?}
    K -->|No| L[Log Error<br/>Return 500]
    K -->|Yes| M{Generation Success?}
    M -->|No| N[Log Error<br/>Return Partial Response]
    M -->|Yes| O[Return Success Response]
    
    C --> P[End]
    E --> P
    G --> P
    I --> P
    L --> P
    N --> P
    O --> P
    
    style C fill:#ffcccc
    style E fill:#ffcccc
    style G fill:#ffcccc
    style I fill:#ffcccc
    style L fill:#ffcccc
    style N fill:#fff4cc
    style O fill:#ccffcc
```

These diagrams can be rendered using Mermaid support in Markdown viewers like GitHub, GitLab, or documentation tools like MkDocs.
