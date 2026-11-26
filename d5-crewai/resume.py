import sys
from flow import ArticleFlow

run_id = sys.argv[1]
flow = ArticleFlow()
result = flow.kickoff(restore_from_state_id=run_id)
print("\n=== FINAL DRAFT ===\n", result)