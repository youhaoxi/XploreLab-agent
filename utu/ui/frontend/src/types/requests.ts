export interface UserQuery {
    query: string;
}

export interface UserSwitchAgent {
    config_file: string;
}

export interface UserRequest {
    type: 'query' | 'list_agents' | 'switch_agent';
    content: UserQuery | UserSwitchAgent | null;
}