# Medical Knowledge Base

This folder contains curated medical knowledge documents from permitted official sources
for the MediLens AI knowledge base.

## Permitted Sources (per ARCHITECTURE.md)

1. **MedlinePlus** (medlineplus.gov) - NIH's consumer health information
2. **NIH/NIDDK** (niddk.nih.gov) - National Institute of Diabetes and Digestive and Kidney Diseases
3. **NHS** (nhs.uk) - UK National Health Service
4. **WHO** (who.int) - World Health Organization

## Documents

Each document includes:
- Source URL and access date
- Content extracted per robots.txt/terms of service
- Topic metadata for retrieval

## Usage

These documents are ingested into the Qdrant `trusted_knowledge` collection
for RAG retrieval. The ingestion process:
1. Parses documents using LlamaIndex
2. Chunks semantically using sentence splitter
3. Generates BGE-small-en-v1.5 embeddings
4. Stores in Qdrant with source provenance
