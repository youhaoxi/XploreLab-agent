""" 
Get phoenix span url by trace_id
"""
from utu.tracing import PhoenixUtils


project_name="test_phoenix"
trace_id = "trace_phoenix_2"
phoenix_utils = PhoenixUtils(project_name=project_name)
print(phoenix_utils.get_trace_url_by_id(trace_id))
