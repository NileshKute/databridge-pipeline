"""
Seed the DataBridge database with sample data for development.

Usage (from the backend/ directory):
    python -m scripts.seed_data

Creates 8 users, 10 transfers in various states, approvals, history, files, and notifications.
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("ENV_FILE", os.path.join(PROJECT_ROOT, ".env"))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.core.config import settings
from backend.app.models.approval import Approval, ApprovalStatus
from backend.app.models.history import TransferHistory
from backend.app.models.notification import Notification, NotificationType
from backend.app.models.transfer import (
    Transfer,
    TransferCategory,
    TransferFile,
    TransferPriority,
    TransferStatus,
)
from backend.app.models.user import User, UserRole

NOW = datetime.now(timezone.utc)


def _t(**kwargs: int) -> datetime:
    """Helper: NOW minus timedelta."""
    return NOW - timedelta(**kwargs)


# ── Users (matching fallback authenticator) ──────────────────────────────────

USERS = [
    {
        "username": "artist1",
        "display_name": "Sarah Chen",
        "email": "sarah.chen@studio.local",
        "role": UserRole.ARTIST,
        "department": "VFX",
        "title": "VFX Artist",
    },
    {
        "username": "artist2",
        "display_name": "James Park",
        "email": "james.park@studio.local",
        "role": UserRole.ARTIST,
        "department": "Animation",
        "title": "Animator",
    },
    {
        "username": "teamlead1",
        "display_name": "Marcus Johnson",
        "email": "marcus.johnson@studio.local",
        "role": UserRole.TEAM_LEAD,
        "department": "VFX",
        "title": "VFX Team Lead",
    },
    {
        "username": "supervisor1",
        "display_name": "Kim Tanaka",
        "email": "kim.tanaka@studio.local",
        "role": UserRole.SUPERVISOR,
        "department": "VFX",
        "title": "VFX Supervisor",
    },
    {
        "username": "producer1",
        "display_name": "Alex Rivera",
        "email": "alex.rivera@studio.local",
        "role": UserRole.LINE_PRODUCER,
        "department": "Production",
        "title": "Line Producer",
    },
    {
        "username": "datateam1",
        "display_name": "Priya Sharma",
        "email": "priya.sharma@studio.local",
        "role": UserRole.DATA_TEAM,
        "department": "Data Management",
        "title": "Data Coordinator",
    },
    {
        "username": "it1",
        "display_name": "Tom Wilson",
        "email": "tom.wilson@studio.local",
        "role": UserRole.IT_TEAM,
        "department": "IT",
        "title": "Systems Engineer",
    },
    {
        "username": "admin1",
        "display_name": "Root Admin",
        "email": "admin@studio.local",
        "role": UserRole.ADMIN,
        "department": "IT",
        "title": "System Administrator",
    },
]


async def seed(session: AsyncSession) -> None:
    # Check if data already exists
    existing = (await session.execute(select(User).limit(1))).scalar_one_or_none()
    if existing:
        print("Database already has data — skipping seed.")
        print("To re-seed, drop all tables first: alembic downgrade base && alembic upgrade head")
        return

    # ── Create users ─────────────────────────────────────────────────────
    users: dict[str, User] = {}
    for u in USERS:
        user = User(**u, is_active=True, created_at=_t(days=90), updated_at=_t(days=1))
        session.add(user)
        users[u["username"]] = user
    await session.flush()

    sarah = users["artist1"]      # artist
    james = users["artist2"]      # artist
    marcus = users["teamlead1"]   # team_lead
    kim = users["supervisor1"]    # supervisor
    alex = users["producer1"]     # line_producer
    priya = users["datateam1"]    # data_team
    tom = users["it1"]            # it_team

    print(f"Created {len(users)} users")

    # ── Helper to add approvals ──────────────────────────────────────────
    def make_approvals(
        transfer: Transfer,
        *,
        tl: str = "pending",
        sv: str = "pending",
        lp: str = "pending",
        dt: str = "pending",
        it: str = "pending",
        tl_by: User | None = None,
        sv_by: User | None = None,
        lp_by: User | None = None,
        tl_comment: str | None = None,
        sv_comment: str | None = None,
        lp_comment: str | None = None,
        tl_at: datetime | None = None,
        sv_at: datetime | None = None,
        lp_at: datetime | None = None,
    ) -> list[Approval]:
        status_map = {
            "pending": ApprovalStatus.PENDING,
            "approved": ApprovalStatus.APPROVED,
            "rejected": ApprovalStatus.REJECTED,
            "skipped": ApprovalStatus.SKIPPED,
        }
        chain = [
            Approval(
                transfer=transfer, required_role=UserRole.TEAM_LEAD,
                status=status_map[tl], approver_id=tl_by.id if tl_by else None,
                comment=tl_comment, decided_at=tl_at, created_at=transfer.created_at,
            ),
            Approval(
                transfer=transfer, required_role=UserRole.SUPERVISOR,
                status=status_map[sv], approver_id=sv_by.id if sv_by else None,
                comment=sv_comment, decided_at=sv_at, created_at=transfer.created_at,
            ),
            Approval(
                transfer=transfer, required_role=UserRole.LINE_PRODUCER,
                status=status_map[lp], approver_id=lp_by.id if lp_by else None,
                comment=lp_comment, decided_at=lp_at, created_at=transfer.created_at,
            ),
            Approval(
                transfer=transfer, required_role=UserRole.DATA_TEAM,
                status=status_map[dt], created_at=transfer.created_at,
            ),
            Approval(
                transfer=transfer, required_role=UserRole.IT_TEAM,
                status=status_map[it], created_at=transfer.created_at,
            ),
        ]
        for a in chain:
            session.add(a)
        return chain

    # ── Helper for files ─────────────────────────────────────────────────
    def make_files(transfer: Transfer, names: list[str], sizes: list[int], scan: str = "pending") -> list[TransferFile]:
        files = []
        for name, size in zip(names, sizes):
            f = TransferFile(
                transfer=transfer,
                filename=name,
                original_path=f"/mnt/staging/{transfer.reference}/{name}",
                size_bytes=size,
                checksum_sha256="a" * 64 if scan == "clean" else None,
                virus_scan_status=scan,
                uploaded_at=transfer.created_at + timedelta(minutes=5),
            )
            session.add(f)
            files.append(f)
        return files

    # ── Helper for history ───────────────────────────────────────────────
    def add_history(transfer: Transfer, user: User | None, action: str, desc: str, at: datetime) -> None:
        session.add(TransferHistory(
            transfer=transfer,
            user_id=user.id if user else None,
            action=action,
            description=desc,
            created_at=at,
        ))

    # ── Helper for notifications ─────────────────────────────────────────
    def add_notif(user: User, transfer: Transfer, ntype: NotificationType, title: str, msg: str, at: datetime, read: bool = False) -> None:
        session.add(Notification(
            user_id=user.id, transfer_id=transfer.id, type=ntype,
            title=title, message=msg, is_read=read, created_at=at,
        ))

    # ══════════════════════════════════════════════════════════════════════
    # TRF-00001: pending_supervisor — TL approved
    # ══════════════════════════════════════════════════════════════════════
    t1 = Transfer(
        reference="TRF-00001", name="Scene_042_Final_v3",
        category=TransferCategory.VFX_ASSETS, status=TransferStatus.PENDING_SUPERVISOR,
        priority=TransferPriority.NORMAL, artist_id=sarah.id,
        total_files=3, total_size_bytes=2_500_000_000,
        staging_path="/mnt/staging/TRF-00001",
        created_at=_t(days=3), updated_at=_t(hours=6),
    )
    session.add(t1)
    await session.flush()
    make_approvals(t1, tl="approved", tl_by=marcus, tl_comment="Looks good", tl_at=_t(days=2, hours=18))
    make_files(t1, ["scene_042_beauty.exr", "scene_042_depth.exr", "scene_042_data.exr"], [900_000_000, 800_000_000, 800_000_000])
    add_history(t1, sarah, "created", "Transfer created", _t(days=3))
    add_history(t1, sarah, "uploaded", "3 files uploaded (2.5 GB)", _t(days=3) + timedelta(minutes=10))
    add_history(t1, marcus, "approved", "Team Lead approved: Looks good", _t(days=2, hours=18))
    add_notif(kim, t1, NotificationType.APPROVAL_REQUIRED, "Approval needed: Scene_042_Final_v3", "Awaiting your supervisor review", _t(days=2, hours=18))

    # ══════════════════════════════════════════════════════════════════════
    # TRF-00002: pending_team_lead — just submitted
    # ══════════════════════════════════════════════════════════════════════
    t2 = Transfer(
        reference="TRF-00002", name="Char_Dragon_Textures",
        category=TransferCategory.TEXTURES, status=TransferStatus.PENDING_TEAM_LEAD,
        priority=TransferPriority.NORMAL, artist_id=james.id,
        total_files=8, total_size_bytes=4_200_000_000,
        staging_path="/mnt/staging/TRF-00002",
        created_at=_t(days=1), updated_at=_t(hours=2),
    )
    session.add(t2)
    await session.flush()
    make_approvals(t2)
    make_files(t2,
        ["dragon_diffuse_4k.tif", "dragon_spec_4k.tif", "dragon_normal_4k.tif", "dragon_disp_4k.tif",
         "dragon_sss_4k.tif", "dragon_bump_4k.tif", "dragon_mask_4k.tif", "dragon_ao_4k.tif"],
        [600_000_000, 550_000_000, 520_000_000, 510_000_000, 500_000_000, 500_000_000, 510_000_000, 510_000_000])
    add_history(t2, james, "created", "Transfer created", _t(days=1))
    add_history(t2, james, "uploaded", "8 files uploaded (4.2 GB)", _t(days=1) + timedelta(minutes=15))
    add_notif(marcus, t2, NotificationType.APPROVAL_REQUIRED, "Approval needed: Char_Dragon_Textures", "James Park submitted textures for review", _t(days=1) + timedelta(minutes=15))

    # ══════════════════════════════════════════════════════════════════════
    # TRF-00003: scanning — all 3 approvals done
    # ══════════════════════════════════════════════════════════════════════
    t3 = Transfer(
        reference="TRF-00003", name="Env_Forest_Lighting",
        category=TransferCategory.LIGHTING, status=TransferStatus.SCANNING,
        priority=TransferPriority.HIGH, artist_id=sarah.id,
        total_files=5, total_size_bytes=1_800_000_000,
        staging_path="/mnt/staging/TRF-00003",
        scan_started_at=_t(hours=3),
        created_at=_t(days=5), updated_at=_t(hours=3),
    )
    session.add(t3)
    await session.flush()
    make_approvals(t3,
        tl="approved", tl_by=marcus, tl_at=_t(days=4, hours=12),
        sv="approved", sv_by=kim, sv_comment="Excellent work", sv_at=_t(days=4),
        lp="approved", lp_by=alex, lp_at=_t(days=3, hours=12),
        dt="pending", it="pending",
    )
    make_files(t3,
        ["forest_key.exr", "forest_fill.exr", "forest_rim.exr", "forest_bounce.exr", "forest_hdri.hdr"],
        [400_000_000, 350_000_000, 350_000_000, 350_000_000, 350_000_000], scan="pending")
    add_history(t3, sarah, "created", "Transfer created", _t(days=5))
    add_history(t3, marcus, "approved", "Team Lead approved", _t(days=4, hours=12))
    add_history(t3, kim, "approved", "Supervisor approved: Excellent work", _t(days=4))
    add_history(t3, alex, "approved", "Line Producer approved", _t(days=3, hours=12))
    add_history(t3, priya, "scan_started", "Virus scan started", _t(hours=3))
    add_notif(priya, t3, NotificationType.SCAN_STARTED, "Scan started: Env_Forest_Lighting", "Virus scan in progress", _t(hours=3))

    # ══════════════════════════════════════════════════════════════════════
    # TRF-00004: transferred — complete pipeline
    # ══════════════════════════════════════════════════════════════════════
    t4 = Transfer(
        reference="TRF-00004", name="Audio_Score_Ep3",
        category=TransferCategory.AUDIO, status=TransferStatus.TRANSFERRED,
        priority=TransferPriority.NORMAL, artist_id=james.id,
        total_files=2, total_size_bytes=350_000_000,
        staging_path="/mnt/staging/TRF-00004",
        production_path="/mnt/production/audio/TRF-00004",
        scan_started_at=_t(days=8), scan_completed_at=_t(days=8) + timedelta(hours=1),
        scan_passed=True, scan_result={"files_scanned": 2, "threats": 0},
        transfer_started_at=_t(days=7, hours=12), transfer_completed_at=_t(days=7, hours=11),
        transfer_verified=True, transfer_method="rsync",
        created_at=_t(days=10), updated_at=_t(days=7, hours=11),
    )
    session.add(t4)
    await session.flush()
    make_approvals(t4,
        tl="approved", tl_by=marcus, tl_at=_t(days=9, hours=12),
        sv="approved", sv_by=kim, sv_at=_t(days=9),
        lp="approved", lp_by=alex, lp_at=_t(days=8, hours=12),
        dt="approved", it="approved",
    )
    make_files(t4, ["ep3_score_master.wav", "ep3_score_stems.wav"], [200_000_000, 150_000_000], scan="clean")
    add_history(t4, james, "created", "Transfer created", _t(days=10))
    add_history(t4, marcus, "approved", "Team Lead approved", _t(days=9, hours=12))
    add_history(t4, kim, "approved", "Supervisor approved", _t(days=9))
    add_history(t4, alex, "approved", "Line Producer approved", _t(days=8, hours=12))
    add_history(t4, None, "scan_passed", "Virus scan passed: 0 threats", _t(days=8))
    add_history(t4, tom, "transfer_started", "Transfer started via rsync", _t(days=7, hours=12))
    add_history(t4, None, "verified", "Checksums verified", _t(days=7, hours=11))
    add_notif(james, t4, NotificationType.TRANSFER_COMPLETE, "Transfer complete: Audio_Score_Ep3", "Your files are now in production", _t(days=7, hours=11), read=True)

    # ══════════════════════════════════════════════════════════════════════
    # TRF-00005: rejected — TL approved, SV rejected
    # ══════════════════════════════════════════════════════════════════════
    t5 = Transfer(
        reference="TRF-00005", name="Anim_Fight_Seq_v4",
        category=TransferCategory.ANIMATION, status=TransferStatus.REJECTED,
        priority=TransferPriority.HIGH, artist_id=sarah.id,
        total_files=4, total_size_bytes=3_100_000_000,
        staging_path="/mnt/staging/TRF-00005",
        rejection_reason="Frame range is incorrect — expected 1001-1150, got 1001-1100. Please re-export with the correct range.",
        created_at=_t(days=4), updated_at=_t(days=2),
    )
    session.add(t5)
    await session.flush()
    make_approvals(t5,
        tl="approved", tl_by=marcus, tl_at=_t(days=3, hours=12),
        sv="rejected", sv_by=kim, sv_comment="Frame range is incorrect — expected 1001-1150, got 1001-1100. Please re-export with the correct range.", sv_at=_t(days=2),
    )
    make_files(t5,
        ["fight_anim_v4.abc", "fight_anim_v4.fbx", "fight_ref_v4.mov", "fight_notes.txt"],
        [1_200_000_000, 1_000_000_000, 850_000_000, 50_000_000])
    add_history(t5, sarah, "created", "Transfer created", _t(days=4))
    add_history(t5, marcus, "approved", "Team Lead approved", _t(days=3, hours=12))
    add_history(t5, kim, "rejected", "Supervisor rejected: Frame range incorrect", _t(days=2))
    add_notif(sarah, t5, NotificationType.REJECTED, "Transfer rejected: Anim_Fight_Seq_v4", "Kim Tanaka rejected — incorrect frame range", _t(days=2))

    # ══════════════════════════════════════════════════════════════════════
    # TRF-00006: pending_line_producer — TL+SV approved, urgent
    # ══════════════════════════════════════════════════════════════════════
    t6 = Transfer(
        reference="TRF-00006", name="Comp_Explosion_Final",
        category=TransferCategory.COMPOSITING, status=TransferStatus.PENDING_LINE_PRODUCER,
        priority=TransferPriority.URGENT, artist_id=sarah.id,
        total_files=6, total_size_bytes=5_500_000_000,
        staging_path="/mnt/staging/TRF-00006",
        notes="Deadline: end of day Friday. Client review on Monday.",
        created_at=_t(days=2), updated_at=_t(hours=8),
    )
    session.add(t6)
    await session.flush()
    make_approvals(t6,
        tl="approved", tl_by=marcus, tl_comment="Urgent — fast-tracking", tl_at=_t(days=1, hours=18),
        sv="approved", sv_by=kim, sv_at=_t(days=1, hours=12),
    )
    make_files(t6,
        ["explosion_beauty.exr", "explosion_alpha.exr", "explosion_depth.exr",
         "explosion_motion.exr", "explosion_crypto.exr", "explosion_preview.mov"],
        [1_200_000_000, 900_000_000, 900_000_000, 900_000_000, 800_000_000, 800_000_000])
    add_history(t6, sarah, "created", "Transfer created (URGENT)", _t(days=2))
    add_history(t6, marcus, "approved", "Team Lead approved: Urgent — fast-tracking", _t(days=1, hours=18))
    add_history(t6, kim, "approved", "Supervisor approved", _t(days=1, hours=12))
    add_notif(alex, t6, NotificationType.APPROVAL_REQUIRED, "URGENT: Comp_Explosion_Final", "Awaiting your Line Producer approval", _t(days=1, hours=12))

    # ══════════════════════════════════════════════════════════════════════
    # TRF-00007: transferred — older completed transfer
    # ══════════════════════════════════════════════════════════════════════
    t7 = Transfer(
        reference="TRF-00007", name="Env_City_Assets",
        category=TransferCategory.VFX_ASSETS, status=TransferStatus.TRANSFERRED,
        priority=TransferPriority.NORMAL, artist_id=james.id,
        total_files=12, total_size_bytes=8_200_000_000,
        staging_path="/mnt/staging/TRF-00007",
        production_path="/mnt/production/vfx_assets/TRF-00007",
        scan_started_at=_t(days=16), scan_completed_at=_t(days=16) + timedelta(hours=2),
        scan_passed=True, scan_result={"files_scanned": 12, "threats": 0},
        transfer_started_at=_t(days=15), transfer_completed_at=_t(days=15) + timedelta(hours=3),
        transfer_verified=True, transfer_method="rsync",
        created_at=_t(days=20), updated_at=_t(days=15),
    )
    session.add(t7)
    await session.flush()
    make_approvals(t7,
        tl="approved", tl_by=marcus, tl_at=_t(days=19),
        sv="approved", sv_by=kim, sv_at=_t(days=18),
        lp="approved", lp_by=alex, lp_at=_t(days=17),
        dt="approved", it="approved",
    )
    city_files = [f"city_block_{i:02d}.usd" for i in range(1, 13)]
    city_sizes = [700_000_000 - i * 5_000_000 for i in range(12)]
    make_files(t7, city_files, city_sizes, scan="clean")
    add_history(t7, james, "created", "Transfer created", _t(days=20))
    add_history(t7, None, "verified", "Checksums verified — transfer complete", _t(days=15))
    add_notif(james, t7, NotificationType.TRANSFER_COMPLETE, "Transfer complete: Env_City_Assets", "12 files delivered to production", _t(days=15), read=True)

    # ══════════════════════════════════════════════════════════════════════
    # TRF-00008: pending_team_lead — high priority
    # ══════════════════════════════════════════════════════════════════════
    t8 = Transfer(
        reference="TRF-00008", name="Char_Hero_Rig_v5",
        category=TransferCategory.ANIMATION, status=TransferStatus.PENDING_TEAM_LEAD,
        priority=TransferPriority.HIGH, artist_id=james.id,
        total_files=3, total_size_bytes=1_600_000_000,
        staging_path="/mnt/staging/TRF-00008",
        notes="Updated rig with fixed IK constraints",
        created_at=_t(hours=12), updated_at=_t(hours=12),
    )
    session.add(t8)
    await session.flush()
    make_approvals(t8)
    make_files(t8, ["hero_rig_v5.ma", "hero_rig_v5.abc", "hero_ref_sheet.pdf"], [800_000_000, 700_000_000, 100_000_000])
    add_history(t8, james, "created", "Transfer created", _t(hours=12))
    add_history(t8, james, "uploaded", "3 files uploaded (1.6 GB)", _t(hours=12) + timedelta(minutes=8))
    add_notif(marcus, t8, NotificationType.APPROVAL_REQUIRED, "Approval needed: Char_Hero_Rig_v5", "High priority — James Park submitted new rig", _t(hours=12))

    # ══════════════════════════════════════════════════════════════════════
    # TRF-00009: approved — ready for scan
    # ══════════════════════════════════════════════════════════════════════
    t9 = Transfer(
        reference="TRF-00009", name="Tex_Vehicle_Pack",
        category=TransferCategory.TEXTURES, status=TransferStatus.APPROVED,
        priority=TransferPriority.NORMAL, artist_id=sarah.id,
        total_files=20, total_size_bytes=6_000_000_000,
        staging_path="/mnt/staging/TRF-00009",
        created_at=_t(days=6), updated_at=_t(days=2),
    )
    session.add(t9)
    await session.flush()
    make_approvals(t9,
        tl="approved", tl_by=marcus, tl_at=_t(days=5),
        sv="approved", sv_by=kim, sv_at=_t(days=4),
        lp="approved", lp_by=alex, lp_at=_t(days=3),
    )
    tex_files = [f"vehicle_tex_{i:02d}_4k.tif" for i in range(1, 21)]
    tex_sizes = [300_000_000] * 20
    make_files(t9, tex_files, tex_sizes)
    add_history(t9, sarah, "created", "Transfer created", _t(days=6))
    add_history(t9, marcus, "approved", "Team Lead approved", _t(days=5))
    add_history(t9, kim, "approved", "Supervisor approved", _t(days=4))
    add_history(t9, alex, "approved", "Line Producer approved", _t(days=3))
    add_notif(priya, t9, NotificationType.APPROVAL_REQUIRED, "Ready for scan: Tex_Vehicle_Pack", "Approved transfer awaiting data team scan", _t(days=2))

    # ══════════════════════════════════════════════════════════════════════
    # TRF-00010: uploaded — just submitted
    # ══════════════════════════════════════════════════════════════════════
    t10 = Transfer(
        reference="TRF-00010", name="Light_Interior_v2",
        category=TransferCategory.LIGHTING, status=TransferStatus.UPLOADED,
        priority=TransferPriority.LOW, artist_id=sarah.id,
        total_files=2, total_size_bytes=900_000_000,
        staging_path="/mnt/staging/TRF-00010",
        notes="Low priority — needed next week",
        created_at=_t(hours=1), updated_at=_t(hours=1),
    )
    session.add(t10)
    await session.flush()
    make_files(t10, ["interior_light_v2.exr", "interior_hdri_v2.hdr"], [600_000_000, 300_000_000])
    add_history(t10, sarah, "created", "Transfer created", _t(hours=1))
    add_history(t10, sarah, "uploaded", "2 files uploaded (900 MB)", _t(hours=1) + timedelta(minutes=3))

    await session.commit()
    print("Seed data inserted successfully!")
    print("  8 users, 10 transfers, approvals, history, files, notifications")


async def main() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        await seed(session)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
