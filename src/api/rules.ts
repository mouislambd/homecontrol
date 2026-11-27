import { apiFetch } from './client'
import { API_ENDPOINTS } from '../config/api'
import type { AutomationRule, RulePayload } from '../types'

export async function fetchRules(): Promise<AutomationRule[]> {
  const payload = await apiFetch<{ rules: AutomationRule[] }>(API_ENDPOINTS.rules)
  return payload.rules
}

export async function createRule(payload: RulePayload): Promise<AutomationRule> {
  return apiFetch<AutomationRule>(API_ENDPOINTS.rules, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateRule(
  id: string,
  payload: Partial<RulePayload>,
): Promise<AutomationRule> {
  return apiFetch<AutomationRule>(API_ENDPOINTS.rule(id), {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export async function deleteRule(id: string): Promise<void> {
  await apiFetch<null>(API_ENDPOINTS.rule(id), { method: 'DELETE' })
}
