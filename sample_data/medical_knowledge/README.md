# Medical Knowledge

Sample trusted medical knowledge content for development.

## Sources (permitted only)

- MedlinePlus (NIH)
- WHO publications
- NHS Health A-Z
- NIH resources
- NIDDK

## Structure

- `sources.json` - Source URLs and metadata
- `sample_content/` - Sample parsed content
  - `{source}_{topic}.json` - Parsed and chunked content

## Format

Each knowledge chunk includes:
- `title` - Article title
- `publisher` - Source organization
- `url` - Original URL
- `publication_date` - When published
- `retrieval_date` - When fetched
- `topic` - Medical topic
- `content` - Cleaned text content
- `chunk_index` - Position in original document

## Note

This directory contains development samples only.
Production knowledge ingestion runs through the ingestion pipeline.
