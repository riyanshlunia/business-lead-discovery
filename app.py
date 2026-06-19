import os
import json
import asyncio
import logging
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

from src.scraper.osm_scraper import OSMScraper
from src.scraper.website_checker import WebsiteChecker
from src.scraper.website_finder import WebsiteFinder
from src.scraper.online_presence_scorer import OnlinePresenceScorer
from src.processor.data_cleaner import DataCleaner
from src.ai_analysis.business_analyzer import BusinessAnalyzer
from src.sheets.google_sheets_client import GoogleSheetsClient

logger = logging.getLogger(__name__)

load_dotenv()

SAVE_LOCAL_CSV = os.getenv("SAVE_LOCAL_CSV", "false").lower() in ("1", "true", "yes")

app = FastAPI(title="LeadForge API", description="AI-Powered Business Lead Discovery")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "LeadForge API is running. Visit /docs for the API explorer."}


def _sse(event_type: str, data: dict) -> str:
    """Format a Server-Sent Event message."""
    return f"data: {json.dumps({'type': event_type, **data})}\n\n"


# ── Column ordering for final output ─────────────────────────────────────────
FINAL_COLUMNS = [
    "Business Name", "Category", "Location",
    "Website Status", "Website URL",
    "Discovery Method", "Confidence Score", "Validation Signals",
    "Search Query Used", "Discovery Status",
    "Digital Presence Score", "Lead Opportunity Score", "Potential Category",
    "Social Channels", "Presence Breakdown",
    "Facebook URL", "Instagram URL", "Twitter URL",
    "LinkedIn URL", "YouTube URL", "Wikipedia URL", "TripAdvisor URL",
    "Phone Number", "Email Address",
    "AI Insight",
    "Google Maps Profile Link",
]


async def _discovery_generator(industry: str, location: str, max_results: int):
    """Async generator that streams SSE progress events + final results."""
    try:
        # ── Step 1: Scrape ────────────────────────────────────────────────
        try:
            logger.info("Yielding: Searching OpenStreetMap for businesses")
            yield _sse("progress", {"step": 1, "label": "Searching OpenStreetMap for businesses…", "pct": 8})
            logger.info("Returned from yield: Searching OpenStreetMap for businesses")
            await asyncio.sleep(0)

            scraper = OSMScraper()
            logger.info("Calling OSMScraper.search_businesses")
            raw_data = await asyncio.get_event_loop().run_in_executor(
                None, lambda: scraper.search_businesses(industry, location, max_results=max_results)
            )
            logger.info("Returned from OSMScraper.search_businesses")

            if not raw_data:
                logger.info("Yielding: No businesses found error")
                yield _sse("error", {
                    "message": (
                        f"No businesses found for '{industry}' in '{location}'. "
                        "Try a different industry keyword or a larger city."
                    )
                })
                logger.info("Returned from yield: No businesses found error")
                return

            logger.info("Yielding: Found businesses on OpenStreetMap")
            yield _sse("progress", {
                "step": 1, "done": True, "pct": 18,
                "label": f"Found {len(raw_data)} businesses on OpenStreetMap ✓",
            })
            logger.info("Returned from yield: Found businesses on OpenStreetMap")
        except Exception:
            logger.exception("Stage failed: Searching OpenStreetMap for businesses")
            raise

        # ── Step 1b: Validate OSM websites + discover missing ones ─────
        try:
            logger.info("Yielding: Validating & discovering business websites")
            yield _sse("progress", {
                "step": 1, "label": "Validating & discovering business websites…", "pct": 20,
            })
            logger.info("Returned from yield: Validating & discovering business websites")
            await asyncio.sleep(0)
            before_count = sum(1 for r in raw_data if r.get("Website URL"))
            finder = WebsiteFinder(delay=1.2)
            logger.info("Calling website_finder.enrich_records")
            raw_data = await asyncio.get_event_loop().run_in_executor(
                None, lambda: finder.enrich_records(raw_data, location)
            )
            logger.info("Returned from website_finder.enrich_records")
            after_count = sum(1 for r in raw_data if r.get("Website URL"))
            logger.info("Yielding: Website check done")
            yield _sse("progress", {
                "step": 1, "done": True, "pct": 22,
                "label": f"Website check done — {after_count} businesses with verified websites ✓",
            })
            logger.info("Returned from yield: Website check done")
        except Exception:
            logger.exception("Stage failed: Validating & discovering business websites")
            raise

        # ── Step 2: Clean ─────────────────────────────────────────────────
        try:
            logger.info("Yielding: Cleaning & de-duplicating data")
            yield _sse("progress", {"step": 2, "label": "Cleaning & de-duplicating data…", "pct": 26})
            logger.info("Returned from yield: Cleaning & de-duplicating data")
            await asyncio.sleep(0)

            cleaner = DataCleaner()
            logger.info("Calling DataCleaner.clean_data")
            df = cleaner.clean_data(raw_data)
            logger.info("Returned from DataCleaner.clean_data")

            logger.info("Yielding: Data cleaned")
            yield _sse("progress", {
                "step": 2, "done": True, "pct": 32,
                "label": f"Data cleaned — {len(df)} unique businesses ✓",
            })
            logger.info("Returned from yield: Data cleaned")
        except Exception:
            logger.exception("Stage failed: Cleaning & de-duplicating data")
            raise

        # ── Step 3: Website checking ──────────────────────────────────────
        try:
            logger.info("Yielding: Checking website quality")
            yield _sse("progress", {"step": 3, "label": "Checking website quality…", "pct": 36})
            logger.info("Returned from yield: Checking website quality")
            await asyncio.sleep(0)

            checker = WebsiteChecker()
            logger.info("Calling WebsiteChecker.check_website for dataframe URLs")
            website_statuses = await asyncio.get_event_loop().run_in_executor(
                None, lambda: [checker.check_website(url) for url in df["Website URL"]]
            )
            logger.info("Returned from WebsiteChecker.check_website for dataframe URLs")
            df["Website Status"] = website_statuses

            no_web = sum(1 for s in website_statuses if s == "No Website")
            logger.info("Yielding: Website check done")
            yield _sse("progress", {
                "step": 3, "done": True, "pct": 55,
                "label": f"Website check done — {no_web} businesses with no website ✓",
            })
            logger.info("Returned from yield: Website check done")
        except Exception:
            logger.exception("Stage failed: Checking website quality")
            raise

        # ── Step 4: Online presence scoring ──────────────────────────────
        try:
            logger.info("Yielding: Scoring online presence")
            yield _sse("progress", {"step": 4, "label": "Scoring online presence…", "pct": 60})
            logger.info("Returned from yield: Scoring online presence")
            await asyncio.sleep(0)

            scorer = OnlinePresenceScorer()
            logger.info("Calling OnlinePresenceScorer.score across dataframe")
            score_rows = df.apply(
                lambda row: scorer.score(row.to_dict(), row["Website Status"]), axis=1
            )
            logger.info("Returned from OnlinePresenceScorer.score across dataframe")
            for col in ["Digital Presence Score", "Lead Opportunity Score", "Social Channels", "Presence Breakdown"]:
                df[col] = [r[col] for r in score_rows]

            df["Potential Category"] = df["Lead Opportunity Score"].apply(
                OnlinePresenceScorer.opportunity_to_priority
            )

            logger.info("Yielding: Online presence scored")
            yield _sse("progress", {
                "step": 4, "done": True, "pct": 68,
                "label": "Online presence scored ✓",
            })
            logger.info("Returned from yield: Online presence scored")
        except Exception:
            logger.exception("Stage failed: Scoring online presence")
            raise

        # ── Step 5: AI Insights ───────────────────────────────────────────
        try:
            logger.info("Yielding: Generating AI insights for each lead")
            yield _sse("progress", {"step": 5, "label": "Generating AI insights for each lead…", "pct": 72})
            logger.info("Returned from yield: Generating AI insights for each lead")
            await asyncio.sleep(0)

            analyzer = BusinessAnalyzer()

            def _analyze_all(df):
                insights = []
                for _, row in df.iterrows():
                    insight = analyzer.analyze_opportunity(
                        business_name=row["Business Name"],
                        industry=industry,
                        website_status=row["Website Status"],
                        social_channels=row.get("Social Channels", ""),
                        digital_score=int(row.get("Digital Presence Score", 0)),
                    )
                    insights.append(insight)
                return insights

            logger.info("Calling BusinessAnalyzer.analyze_opportunity across dataframe")
            ai_insights = await asyncio.get_event_loop().run_in_executor(None, lambda: _analyze_all(df))
            logger.info("Returned from BusinessAnalyzer.analyze_opportunity across dataframe")
            df["AI Insight"] = ai_insights

            logger.info("Yielding: AI insights generated")
            yield _sse("progress", {
                "step": 5, "done": True, "pct": 84,
                "label": "AI insights generated ✓",
            })
            logger.info("Returned from yield: AI insights generated")
        except Exception:
            logger.exception("Stage failed: Generating AI insights for each lead")
            raise

        # ── Step 6: Sort & finalise columns ──────────────────────────────
        try:
            logger.info("Calling DataFrame sort/finalise stage")
            df = df.sort_values("Lead Opportunity Score", ascending=False).reset_index(drop=True)
            df = df[[c for c in FINAL_COLUMNS if c in df.columns]]
            logger.info("Returned from DataFrame sort/finalise stage")
        except Exception:
            logger.exception("Stage failed: Sort & finalise columns")
            raise

        # ── Step 7: Export ────────────────────────────────────────────────
        try:
            logger.info("Yielding: Exporting to Google Sheets")
            yield _sse("progress", {"step": 6, "label": "Exporting to Google Sheets…", "pct": 88})
            logger.info("Returned from yield: Exporting to Google Sheets")
            await asyncio.sleep(0)

            sheet_id = os.getenv("GOOGLE_SHEET_ID")
            try:
                sheets_client = GoogleSheetsClient()
                logger.info("Calling GoogleSheetsClient.export_to_sheet")
                await asyncio.get_event_loop().run_in_executor(
                    None, lambda: sheets_client.export_to_sheet(df)
                )
                logger.info("Returned from GoogleSheetsClient.export_to_sheet")
            except Exception as e:
                sheet_id = None
                print(f"Google Sheets export failed (non-fatal): {e}")

            if SAVE_LOCAL_CSV:
                os.makedirs("data", exist_ok=True)
                safe = lambda s: "".join(c if c.isalnum() else "_" for c in s)
                csv_path = os.path.join("data", f"{safe(industry)}_{safe(location)}_leads.csv")
                df.to_csv(csv_path, index=False)

            logger.info("Yielding: Export complete")
            yield _sse("progress", {
                "step": 6, "done": True, "pct": 96,
                "label": "Export complete ✓",
            })
            logger.info("Returned from yield: Export complete")

            leads = df.fillna("").to_dict(orient="records")

            logger.info("Yielding: done event")
            yield _sse("done", {
                "status": "success",
                "message": f"Found {len(leads)} leads for {industry} in {location}.",
                "exported_to_sheet": sheet_id,
                "leads": leads,
            })
            logger.info("Returned from yield: done event")
        except Exception:
            logger.exception("Stage failed: Export")
            raise

    except Exception as e:
        yield _sse("error", {"message": str(e)})


@app.post("/run/stream")
async def run_stream(
    industry: str = Form(...),
    location: str = Form(...),
    max_results: int = Form(20),
):
    """SSE streaming endpoint — yields live progress + final results."""
    return StreamingResponse(
        _discovery_generator(industry, location, max_results),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/run")
async def run_sync(
    industry: str = Form(...),
    location: str = Form(...),
    max_results: int = Form(20),
):
    """Non-streaming fallback — waits for everything then returns JSON."""
    try:
        scraper = OSMScraper()
        raw_data = scraper.search_businesses(industry, location, max_results=max_results)

        if not raw_data:
            return {"status": "error", "message": f"No businesses found for '{industry}' in '{location}'."}

        # Enrich missing website URLs via web search
        finder = WebsiteFinder(delay=1.2)
        raw_data = finder.enrich_records(raw_data, location)

        cleaner = DataCleaner()
        df = cleaner.clean_data(raw_data)

        checker = WebsiteChecker()
        df["Website Status"] = [checker.check_website(url) for url in df["Website URL"]]

        scorer = OnlinePresenceScorer()
        score_rows = df.apply(lambda row: scorer.score(row.to_dict(), row["Website Status"]), axis=1)
        for col in ["Digital Presence Score", "Lead Opportunity Score", "Social Channels", "Presence Breakdown"]:
            df[col] = [r[col] for r in score_rows]
        df["Potential Category"] = df["Lead Opportunity Score"].apply(
            OnlinePresenceScorer.opportunity_to_priority
        )

        analyzer = BusinessAnalyzer()
        df["AI Insight"] = [
            analyzer.analyze_opportunity(
                row["Business Name"], industry, row["Website Status"],
                row.get("Social Channels", ""), int(row.get("Digital Presence Score", 0))
            )
            for _, row in df.iterrows()
        ]

        df = df.sort_values("Lead Opportunity Score", ascending=False).reset_index(drop=True)
        df = df[[c for c in FINAL_COLUMNS if c in df.columns]]

        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        try:
            sheets_client = GoogleSheetsClient()
            sheets_client.export_to_sheet(df)
        except Exception as e:
            sheet_id = None
            print(f"Sheets export failed (non-fatal): {e}")

        if SAVE_LOCAL_CSV:
            os.makedirs("data", exist_ok=True)
            safe = lambda s: "".join(c if c.isalnum() else "_" for c in s)
            df.to_csv(os.path.join("data", f"{safe(industry)}_{safe(location)}_leads.csv"), index=False)

        leads = df.fillna("").to_dict(orient="records")
        return {
            "status": "success",
            "message": f"Found {len(leads)} leads for {industry} in {location}.",
            "exported_to_sheet": sheet_id,
            "leads": leads,
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}