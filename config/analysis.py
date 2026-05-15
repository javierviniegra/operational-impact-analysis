from dataclasses import dataclass
from dotenv import load_dotenv
import os

load_dotenv()

@dataclass(frozen=True)
class AnalysisScope:
    wansoft_subsidiary_id: int
    wansoft_branch_name: str
    branch_keyword: str
    zenput_location_name: str
    zenput_account_name: str
    zenput_account_keyword: str
    start_date: str
    end_date: str

def get_scope() -> AnalysisScope:
    return AnalysisScope(
        wansoft_subsidiary_id=int(os.getenv("ANALYSIS_WANSOFT_SUBSIDIARY_ID", "0")),
        wansoft_branch_name=os.getenv("ANALYSIS_WANSOFT_BRANCH_NAME", "").strip(),
        branch_keyword=os.getenv("ANALYSIS_BRANCH_KEYWORD", "").strip(),
        zenput_location_name=os.getenv("ANALYSIS_ZENPUT_LOCATION_NAME", "").strip(),
        zenput_account_name=os.getenv("ANALYSIS_ZENPUT_ACCOUNT_NAME", "").strip(),
        zenput_account_keyword=os.getenv("ANALYSIS_ZENPUT_ACCOUNT_KEYWORD", "").strip(),
        start_date=os.getenv("ANALYSIS_START_DATE", ""),
        end_date=os.getenv("ANALYSIS_END_DATE", ""),
    )