# utu_agent_ui

Static frontend pages for utu-agent `WebUIChatbot`

## Installation

1. Install npm packages

```bash
npm install
```

2. Build Python wheel

```bash
uv pip install build
bash ./build.sh
```

You will get a wheel file in the `build` directory.

3. Install the wheel file

```bash
uv pip install utu_agent_ui-0.1.5-py3-none-any.whl
```

Now the `WebUIChatbot` should work.

## Development

After `npm install`, start the development server.

```bash
npm run dev
```
