import uuid
from sqlalchemy.orm import Session
from apps.api.app.models.entities import Project, TopologySnapshot
from engine.compose_parser.parser import ComposeParser
from engine.twin_builder.builder import TwinBuilder
from engine.graph_engine.analyzer import GraphAnalyzer
from apps.api.app.schemas.contracts import TopologyGraph


class ProjectService:
    @staticmethod
    def create_project(db: Session, name: str, yaml_content: str) -> Project:
        # 1. Parse YAML
        parsed = ComposeParser.parse(yaml_content)
        project_id = f"proj_{uuid.uuid4().hex[:8]}"

        # 2. Build and Analyze Topology Graph
        topology = TwinBuilder.build_topology(project_id, parsed)
        topology = GraphAnalyzer.analyze_reachability(topology)

        # 3. Save Project Record
        db_project = Project(
            id=project_id,
            name=name,
            source_yaml=yaml_content,
            source_hash=parsed["hash"],
            warnings_json=parsed["warnings"],
        )
        db.add(db_project)

        # 4. Save Baseline Topology Snapshot
        db_snapshot = TopologySnapshot(
            id=f"snap_{uuid.uuid4().hex[:8]}",
            project_id=project_id,
            version="baseline",
            graph_json=topology.model_dump(),
            compose_yaml=yaml_content,
        )
        db.add(db_snapshot)

        db.commit()
        db.refresh(db_project)
        return db_project

    @staticmethod
    def get_project(db: Session, project_id: str) -> Project | None:
        return db.query(Project).filter(Project.id == project_id).first()

    @staticmethod
    def get_topology(
        db: Session, project_id: str, version: str = "baseline"
    ) -> TopologyGraph | None:
        snapshot = (
            db.query(TopologySnapshot)
            .filter(
                TopologySnapshot.project_id == project_id,
                TopologySnapshot.version == version,
            )
            .first()
        )

        if not snapshot:
            return None

        return TopologyGraph.model_validate(snapshot.graph_json)
