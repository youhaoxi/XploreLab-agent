export interface TextDeltaContent {
  type: 'reason' | 'tool_call' | 'tool_call_output' | 'text';
  delta: string;
  callid?: string;
  argument?: string;
  inprogress?: boolean;
}

export interface ExampleContent {
  query: string;
}

export interface PlanItem {
  analysis: string;
  todo: string[];
}

export interface WorkerItem {
  task: string;
  output: string;
}

export interface ReportItem {
  output: string;
}

export interface NewAgentContent {
  name: string;
}

export interface InitContent {
  type: 'init';
  default_agent: string;
}

export type OrchestraContent =
  | { type: 'plan'; item: PlanItem }
  | { type: 'worker'; item: WorkerItem }
  | { type: 'report'; item: ReportItem };

export interface ListAgentsContent {
  type: 'list_agents';
  agents: string[];
}

export interface SwitchAgentContent {
  type: 'switch_agent';
  ok: boolean;
  name: string;
}

export interface Event {
  type: 'raw' | 'orchestra' | 'finish' | 'example' | 'new' | 'init' | 'list_agents' | 'switch_agent';
  data: TextDeltaContent | OrchestraContent | ExampleContent | NewAgentContent | InitContent | ListAgentsContent | SwitchAgentContent | null;
  requireConfirm?: boolean;
}
