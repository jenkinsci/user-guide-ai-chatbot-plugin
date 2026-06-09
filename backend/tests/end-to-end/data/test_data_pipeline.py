from mock_collector_output_data import (
    COLLECTOR_OUTPUT_DISCOURSE_TOPICS,
    COLLECTOR_OUTPUT_PLUGIN_DOCS,
    COLLECTOR_OUTPUT_REDDIT_THREADS,
    COLLECTOR_OUTPUT_JENKINS_DOCS,
)
from pathlib import Path
from data.collection.collectors import start_collectors
from data.preprocessing.processors import start_processors
from data.formatting.formatters import start_formatters
from data.chunking.chunker import chunker
from data.models import DataSource
import json


def test_data_pipeline(tmp_path: Path):
    SOURCES = [
        DataSource.JENKINS_DOCS,
        DataSource.PLUGIN_DOCS,
        DataSource.DISCOURSE_TOPICS,
        DataSource.REDDIT_THREADS,
    ]

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    raw_dir = output_dir / "raw"
    raw_dir.mkdir()

    # (Mock) Collection Phase
    COLLECTOR_OUTPUTS = {
        DataSource.JENKINS_DOCS: COLLECTOR_OUTPUT_JENKINS_DOCS,
        DataSource.PLUGIN_DOCS: COLLECTOR_OUTPUT_PLUGIN_DOCS,
        DataSource.DISCOURSE_TOPICS: COLLECTOR_OUTPUT_DISCOURSE_TOPICS,
        DataSource.REDDIT_THREADS: COLLECTOR_OUTPUT_REDDIT_THREADS,
    }

    for source in SOURCES:
        (raw_dir / f"{source.value}.json").write_text(
            json.dumps(COLLECTOR_OUTPUTS[source])
        )

    # Preprocessing Phase
    start_processors(SOURCES, output_dir)

    # Formatting Phase
    start_formatters(SOURCES, output_dir)

    # Chunking Phase
    chunker(SOURCES, output_dir)

    # Verifying outputs (chunks)
    chunks_dir = output_dir / "chunks"

    for source in [*[s.value for s in SOURCES], "code_blocks"]:
        source_dir = chunks_dir / source
        assert source_dir.exists()
