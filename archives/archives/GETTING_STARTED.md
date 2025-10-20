# Getting Started with CrawlEnginePro

## What Was Created

### Clean Project Structure
```
~/Desktop/crawlenginepro.mindmate247.com/
├── code/                          # All source code (Git initialized)
│   ├── shared/                    # Shared configurations
│   │   ├── model_registry.py      # Multi-embedding model configs
│   │   └── .env.example           # Environment template
│   ├── services/                  # All microservices
│   │   ├── storage/v1.0.0/        # Milvus operations
│   │   ├── embeddings/v1.0.0/     # Multi-provider embeddings
│   │   ├── metadata/v1.0.0/       # Metadata extraction
│   │   ├── chunking/v1.0.0/       # Text chunking
│   │   └── ingestion_api/         # Main API orchestrator
│   ├── requirements.txt           # Single unified requirements file
│   └── README.md                  # Complete documentation
│
├── deploy/                        # Deployment scripts
│   ├── deploy.sh                  # Deploy code to server
│   ├── server_setup.sh            # Initial server setup
│   └── manage.sh                  # Service management
│
└── local_dev/                     # Local development (optional)
```

### Key Features
- Multi-embedding support (Jina, SambaNova, Nebius)
- Clean separation of concerns
- Single unified requirements.txt
- Simple management scripts
- Git initialized with initial commit

## Next Steps

### Step 1: Deploy to Server
```bash
cd ~/Desktop/crawlenginepro.mindmate247.com
./deploy/deploy.sh
```

### Step 2: SSH to Server and Run Setup
```bash
ssh -i ~/reku631_nebius reku631@89.169.108.8
cd ~/rag_services/code
./deploy/server_setup.sh
```

This will:
- Clean old installations (~/PipeLineServies, ~/venvs, etc.)
- Create single unified venv at ~/rag_services/venv
- Install all dependencies
- Create logs directory at ~/rag_services/logs
- Copy .env.example to .env

### Step 3: Configure API Keys
```bash
# Still on server
nano ~/rag_services/code/shared/.env

# Update these:
JINA_API_KEY=your_jina_key_here
SAMBANOVA_API_KEY=your_sambanova_key_here
```

### Step 4: Start Services
```bash
# Still on server
cd ~/rag_services/code
./deploy/manage.sh start
```

### Step 5: Check Status
```bash
./deploy/manage.sh status
```

You should see:
```
● storage running (PID: xxxx, Port: 8064)
● embeddings running (PID: xxxx, Port: 8063)
● metadata running (PID: xxxx, Port: 8062)
● chunking running (PID: xxxx, Port: 8061)
● ingestion running (PID: xxxx, Port: 8060)
```

### Step 6: Test Multi-Embedding
From your local machine (with SSH tunnel active):

```bash
# SSH tunnel (in separate terminal)
ssh -i ~/reku631_nebius -L 19530:localhost:19530 -L 3000:localhost:3000 -L 8000:localhost:8000 reku631@89.169.108.8

# Test with Jina
curl -X POST "http://localhost:8060/api/v1.0.0/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/JaiShreeRam.md",
    "embedding_model": "jina-embeddings-v3",
    "chunking_strategy": "semantic",
    "max_chunk_size": 1000,
    "chunk_overlap": 100
  }'

# Test with SambaNova
curl -X POST "http://localhost:8060/api/v1.0.0/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/JaiShreeRam.md",
    "embedding_model": "E5-Mistral-7B-Instruct",
    "chunking_strategy": "semantic",
    "max_chunk_size": 1000,
    "chunk_overlap": 100
  }'
```

Collections will be created as:
- `JaiShreeRam_jina_1024`
- `JaiShreeRam_sambanova_4096`

## Management Commands

### On Server
```bash
cd ~/rag_services/code

# Start all services
./deploy/manage.sh start

# Stop all services
./deploy/manage.sh stop

# Check status
./deploy/manage.sh status

# View logs (all services)
./deploy/manage.sh logs

# Follow specific service log
./deploy/manage.sh logs storage
```

### From Local Machine
```bash
cd ~/Desktop/crawlenginepro.mindmate247.com

# Deploy updated code
./deploy/deploy.sh

# Then SSH to server and restart
ssh -i ~/reku631_nebius reku631@89.169.108.8
cd ~/rag_services/code && ./deploy/manage.sh restart
```

## What Changed from Old Setup

### Removed
- Multiple venvs per service (milvus_storage, embeddings_v3, metadata_v3, chunking_v5)
- Pipeline-manager that opened multiple terminals
- Remote-pipeline script
- Conflicting port configurations
- Multiple scattered README files
- Old PipeLineServies directory

### Added
- Single unified venv for all services
- Clean directory structure
- Simple deploy.sh for code deployment
- Simple manage.sh for service control
- Consolidated documentation
- Git repository

## Troubleshooting

### If deployment fails
```bash
# Check what's in the old location
ssh -i ~/reku631_nebius reku631@89.169.108.8 "ls -la ~/"

# Manual cleanup if needed
ssh -i ~/reku631_nebius reku631@89.169.108.8 "rm -rf ~/PipeLineServies ~/venvs"
```

### If services won't start
```bash
# Check logs
ssh -i ~/reku631_nebius reku631@89.169.108.8 "tail -n 50 ~/rag_services/logs/storage.log"

# Check ports
ssh -i ~/reku631_nebius reku631@89.169.108.8 "lsof -i :8060-8064"
```

### If dependencies are missing
```bash
# Reinstall
ssh -i ~/reku631_nebius reku631@89.169.108.8
source ~/rag_services/venv/bin/activate
pip install -r ~/rag_services/code/requirements.txt
```

## Architecture Notes

### All Services Run on Server
- Server IP: 89.169.108.8
- Services: 8060-8064
- Milvus: localhost:19530 (on server)
- LLM Gateway: localhost:8000 (on server)
- Attu UI: localhost:3000 (on server)

### SSH Tunnel for Access
```bash
ssh -i ~/reku631_nebius -L 19530:localhost:19530 -L 3000:localhost:3000 -L 8000:localhost:8000 reku631@89.169.108.8
```

This forwards:
- 19530: Milvus database
- 3000: Attu UI (Milvus web interface)
- 8000: LLM Gateway (Nebius AI Studio)

### Local Development (Optional)
If you want to test locally:
```bash
cd ~/Desktop/crawlenginepro.mindmate247.com/local_dev
python3 -m venv venv
source venv/bin/activate
pip install -r ../code/requirements.txt

# Start SSH tunnel in another terminal
# Then run services locally
```

## Ready to Go!

The clean structure is ready. Follow the steps above to deploy and test.

Key advantages:
- Clear separation between code, deployment, and local dev
- Single source of truth for dependencies
- Simple management scripts
- No more terminal spam
- Clean git history
