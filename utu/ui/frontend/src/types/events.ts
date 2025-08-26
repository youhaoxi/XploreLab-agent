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

export type OrchestraContent = 
  | { type: 'plan'; item: PlanItem }
  | { type: 'worker'; item: WorkerItem }
  | { type: 'report'; item: ReportItem };

export interface Event {
  type: 'raw' | 'orchestra' | 'finish' | 'example' | 'new';
  data: TextDeltaContent | OrchestraContent | ExampleContent | NewAgentContent | null;
  requireConfirm?: boolean;
}
