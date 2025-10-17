# 1. Use an official Python base image
FROM python:3.12

# 2. Install git for cloning the repository
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# 3. Set the working directory
WORKDIR /XploreLab-agent

# 4. Clone the repository into the working directory
RUN git clone https://github.com/youhaoxi/XploreLab-agent.git .

# 5. Install the 'uv' build tool globally
RUN pip install uv

# 6. Synchronize the Python environment and dependencies
RUN uv sync

# 7. Add the virtual environment's bin directory to PATH
ENV PATH="/XploreLab-agent/.venv/bin:$PATH"

# 8. Install the frontend UI package
RUN uv pip install https://github.com/youhaoxi/XploreLab-agent/releases/download/v0.2.0/utu_agent_ui-0.2.0-py3-none-any.whl
# 9. Set the default command to start the example application
CMD ["python", "examples/svg_generator/main_web.py"]
