import { useState } from 'react'
import type { FormEvent } from 'react'
import { createRule, deleteRule, fetchRules, updateRule } from '../api/rules'
import { errorMessage } from '../api/client'
import { Field, inputClass } from '../components/FormFields'
import { Notice } from '../components/Notice'
import { StatePanel } from '../components/StatePanel'
import { useDevices } from '../hooks/useDevices'
import { useFetch } from '../hooks/useFetch'
import type { AutomationRule, DeviceStatus } from '../types'

interface RulesViewProps {
  revision: number
}

export function RulesView({ revision }: RulesViewProps) {
  const rulesState = useFetch(fetchRules, revision)
  const devicesState = useDevices(revision)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [triggerDeviceId, setTriggerDeviceId] = useState('')
  const [triggerStatus, setTriggerStatus] = useState<DeviceStatus>('ON')
  const [targetDeviceId, setTargetDeviceId] = useState('')
  const [targetAction, setTargetAction] = useState<DeviceStatus>('ON')
  const [triggerType, setTriggerType] = useState<'device_state' | 'temperature_above' | 'temperature_below'>('device_state')
  const [threshold, setThreshold] = useState('28')
  const [notice, setNotice] = useState<string | null>(null)
  const [tone, setTone] = useState<'error' | 'success'>('error')
  const [busy, setBusy] = useState(false)

  const rules = rulesState.data ?? []
  const devices = devicesState.data ?? []

  const selectedTrigger = triggerDeviceId || devices[0]?.id || ''
  const selectedTarget =
    targetDeviceId || devices[1]?.id || devices[0]?.id || ''

  const resetForm = () => {
    setEditingId(null)
    setName('')
    setTriggerDeviceId('')
    setTriggerStatus('ON')
    setTargetDeviceId('')
    setTargetAction('ON')
    setTriggerType('device_state')
    setThreshold('28')
  }

  const startEdit = (rule: AutomationRule) => {
    setEditingId(rule.id)
    setName(rule.name)
    setTriggerDeviceId(rule.trigger_device_id)
    setTriggerStatus(rule.trigger_status)
    setTargetDeviceId(rule.target_device_id)
    setTargetAction(rule.target_action)
    setTriggerType(rule.trigger_type)
    setThreshold(String(rule.threshold_c ?? 28))
  }

  const runAction = async (operation: () => Promise<void>) => {
    setBusy(true)
    setNotice(null)
    try {
      await operation()
      await rulesState.reload()
    } catch (err) {
      setTone('error')
      setNotice(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const submit = (event: FormEvent) => {
    event.preventDefault()
    void runAction(async () => {
      const payload = {
        name,
        trigger_device_id: selectedTrigger,
        trigger_status: triggerStatus,
        target_device_id: selectedTarget,
        target_action: targetAction,
        enabled: true,
        trigger_type: triggerType,
        threshold_c: triggerType === 'device_state' ? null : Number(threshold),
      }
      if (editingId) {
        await updateRule(editingId, payload)
        setTone('success')
        setNotice('Rule updated.')
      } else {
        await createRule(payload)
        setTone('success')
        setNotice('Rule created.')
      }
      resetForm()
    })
  }

  const deviceOptions = devices.map((device) => (
    <option key={device.id} value={device.id}>
      {device.name}
    </option>
  ))

  return (
    <section className="mt-10">
      <h2 className="text-2xl font-semibold tracking-tight text-white">Automation rules</h2>
      <p className="mt-1 text-sm text-slate-400">
        When a device reaches a state, automatically act on another device.
      </p>

      <Notice message={notice} tone={tone} onDismiss={() => setNotice(null)} />

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <form
          onSubmit={submit}
          className="rounded-3xl border border-white/[0.07] bg-slate-900/40 p-6 backdrop-blur-xl"
        >
          <h3 className="mb-5 text-sm font-semibold text-white">
            {editingId ? 'Edit rule' : 'New rule'}
          </h3>
          <div className="space-y-4">
            <Field label="Rule name">
              <input
                className={inputClass}
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="e.g. Light starts fan"
                required
              />
            </Field>
            <div className="rounded-2xl border border-white/5 bg-slate-950/40 p-4">
              <p className="mb-3 text-[11px] font-medium uppercase tracking-[0.12em] text-slate-500">
                When this happens
              </p>
              <div className="mb-3 grid gap-3 sm:grid-cols-2">
                <Field label="Condition">
                  <select
                    className={inputClass}
                    value={triggerType}
                    onChange={(event) =>
                      setTriggerType(event.target.value as typeof triggerType)
                    }
                  >
                    <option value="device_state">Device state</option>
                    <option value="temperature_above">Temperature above</option>
                    <option value="temperature_below">Temperature below</option>
                  </select>
                </Field>
                {triggerType !== 'device_state' && (
                  <Field label="Threshold °C (simulated)">
                    <input
                      type="number"
                      className={inputClass}
                      value={threshold}
                      onChange={(event) => setThreshold(event.target.value)}
                    />
                  </Field>
                )}
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <Field label="Trigger device">
                  <select
                    className={inputClass}
                    value={selectedTrigger}
                    onChange={(event) => setTriggerDeviceId(event.target.value)}
                    required
                  >
                    <option value="">Select device</option>
                    {deviceOptions}
                  </select>
                </Field>
                {triggerType === 'device_state' && (
                  <Field label="Becomes">
                    <select
                      className={inputClass}
                      value={triggerStatus}
                      onChange={(event) => setTriggerStatus(event.target.value as DeviceStatus)}
                    >
                      <option value="ON">ON</option>
                      <option value="OFF">OFF</option>
                    </select>
                  </Field>
                )}
              </div>
            </div>
            <div className="rounded-2xl border border-white/5 bg-slate-950/40 p-4">
              <p className="mb-3 text-[11px] font-medium uppercase tracking-[0.12em] text-slate-500">
                Then do this
              </p>
              <div className="grid gap-3 sm:grid-cols-2">
                <Field label="Target device">
                  <select
                    className={inputClass}
                    value={selectedTarget}
                    onChange={(event) => setTargetDeviceId(event.target.value)}
                    required
                  >
                    <option value="">Select device</option>
                    {deviceOptions}
                  </select>
                </Field>
                <Field label="Action">
                  <select
                    className={inputClass}
                    value={targetAction}
                    onChange={(event) => setTargetAction(event.target.value as DeviceStatus)}
                  >
                    <option value="ON">Turn ON</option>
                    <option value="OFF">Turn OFF</option>
                  </select>
                </Field>
              </div>
            </div>
          </div>
          <div className="mt-5 flex gap-2">
            <button
              type="submit"
              disabled={busy}
              className="rounded-full bg-indigo-500/90 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-400 disabled:opacity-50"
            >
              {editingId ? 'Save changes' : 'Create rule'}
            </button>
            {editingId && (
              <button
                type="button"
                onClick={resetForm}
                className="rounded-full border border-white/10 px-4 py-2 text-sm text-slate-300 transition hover:bg-white/5"
              >
                Cancel
              </button>
            )}
          </div>
        </form>

        <div className="rounded-3xl border border-white/[0.07] bg-slate-900/40 p-6 backdrop-blur-xl">
          <StatePanel
            loading={rulesState.loading}
            error={rulesState.error}
            empty={rules.length === 0}
            emptyLabel="No automation rules yet."
            onRetry={() => void rulesState.reload()}
          >
            <div className="space-y-3">
              {rules.map((rule) => (
                <div
                  key={rule.id}
                  className="rounded-2xl border border-white/5 bg-slate-950/40 p-4"
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-medium text-white">{rule.name}</p>
                      <p className="mt-1 text-xs text-slate-500">
                        {rule.trigger_type === 'device_state'
                          ? `${rule.trigger_device_id} ${rule.trigger_status}`
                          : `${rule.trigger_device_id} ${rule.trigger_type.replace('temperature_', 'temp ')} ${rule.threshold_c} °C`}{' '}
                        → {rule.target_device_id} {rule.target_action}
                      </p>
                    </div>
                    <span
                      className={`rounded-full px-2.5 py-1 text-[11px] ${
                        rule.enabled
                          ? 'bg-emerald-400/10 text-emerald-300'
                          : 'bg-slate-400/10 text-slate-400'
                      }`}
                    >
                      {rule.enabled ? 'Active' : 'Paused'}
                    </span>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() =>
                        void runAction(async () => {
                          await updateRule(rule.id, { enabled: !rule.enabled })
                          setTone('success')
                          setNotice('Rule updated.')
                        })
                      }
                      className="rounded-full border border-white/10 px-3 py-1.5 text-xs text-slate-300 transition hover:bg-white/5 disabled:opacity-50"
                    >
                      {rule.enabled ? 'Pause' : 'Resume'}
                    </button>
                    <button
                      type="button"
                      onClick={() => startEdit(rule)}
                      className="rounded-full border border-white/10 px-3 py-1.5 text-xs text-slate-300 transition hover:bg-white/5"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() =>
                        void runAction(async () => {
                          await deleteRule(rule.id)
                          if (editingId === rule.id) resetForm()
                          setTone('success')
                          setNotice('Rule deleted.')
                        })
                      }
                      className="rounded-full border border-rose-400/20 px-3 py-1.5 text-xs text-rose-200 transition hover:bg-rose-400/10 disabled:opacity-50"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </StatePanel>
        </div>
      </div>
    </section>
  )
}
