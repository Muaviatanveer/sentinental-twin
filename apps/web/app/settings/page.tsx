"use client";

import { useEffect, useState } from "react";
import { fetchHealthStatus, updateGemmaConfig } from "@/lib/api";
import { HealthStatusResponse } from "@/lib/types";
import { Sparkles, CheckCircle2, Save } from "lucide-react";

export default function SettingsPage() {
  const [health, setHealth] = useState<HealthStatusResponse | null>(null);
  const [provider, setProvider] = useState("google_genai");
  const [modelName, setModelName] = useState("gemma-4-26b-a4b-it");
  const [apiKey, setApiKey] = useState("");
  const [apiBase, setApiBase] = useState("http://localhost:11434");
  const [savedMsg, setSavedMsg] = useState<string | null>(null);

  useEffect(() => {
    fetchHealthStatus()
      .then((h) => {
        setHealth(h);
        setProvider(h.gemma_provider);
        setModelName(h.gemma_model);
      })
      .catch(() => null);
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavedMsg(null);
    const updated = await updateGemmaConfig({
      provider,
      model_name: modelName,
      api_key: apiKey || undefined,
      api_base: apiBase || undefined,
    });
    setHealth(updated);
    setSavedMsg(`Active: ${updated.gemma_provider} (${updated.gemma_model})`);
  };

  return (
    <div className="max-w-3xl mx-auto p-8 space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-neutral-900">
          Gemma 4 26B A4B & Runtime Settings
        </h1>
        <p className="text-xs text-neutral-500 mt-1">
          Configure live Gemma 4 26B A4B (MoE) inference via Google AI Studio API, Local Ollama, or OpenRouter.
        </p>
      </div>

      <form
        onSubmit={handleSave}
        className="bg-white border border-neutral-200 rounded-lg p-6 space-y-4 text-xs"
      >
        <div className="flex items-center gap-2 text-sm font-semibold text-neutral-900 border-b border-neutral-100 pb-3">
          <Sparkles className="h-4 w-4 text-blue-600" />
          Live Gemma 4 Inference Provider
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block font-medium text-neutral-700 mb-1">
              Inference Provider
            </label>
            <select
              value={provider}
              onChange={(e) => {
                const val = e.target.value;
                setProvider(val);
                if (val === "google_genai") setModelName("gemma-4-26b-a4b-it");
                if (val === "ollama") setModelName("gemma4:26b");
              }}
              className="w-full px-3 py-2 border border-neutral-300 rounded-md bg-white"
            >
              <option value="google_genai">
                Google AI Studio API (gemma-4-26b-a4b-it)
              </option>
              <option value="ollama">Local Ollama (gemma4:26b / Q4_0)</option>
              <option value="openai_compatible">
                OpenRouter / vLLM OpenAI-Compatible
              </option>
              <option value="deterministic_fallback">
                Offline Deterministic Graph Fallback
              </option>
            </select>
          </div>

          <div>
            <label className="block font-medium text-neutral-700 mb-1">
              Gemma 4 Model ID
            </label>
            <input
              type="text"
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              className="w-full px-3 py-2 border border-neutral-300 rounded-md font-mono"
            />
          </div>
        </div>

        {provider === "google_genai" || provider === "openai_compatible" ? (
          <div>
            <label className="block font-medium text-neutral-700 mb-1">
              API Key (Google AI Studio key for <code>gemma-4-26b-a4b-it</code>)
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Paste AIzaSy... key from aistudio.google.com/apikey"
              className="w-full px-3 py-2 border border-neutral-300 rounded-md font-mono"
            />
          </div>
        ) : null}

        {provider === "ollama" || provider === "openai_compatible" ? (
          <div>
            <label className="block font-medium text-neutral-700 mb-1">
              API Base URL
            </label>
            <input
              type="text"
              value={apiBase}
              onChange={(e) => setApiBase(e.target.value)}
              className="w-full px-3 py-2 border border-neutral-300 rounded-md font-mono"
            />
          </div>
        ) : null}

        <div className="flex items-center justify-between pt-2">
          {savedMsg ? (
            <span className="inline-flex items-center gap-1.5 text-emerald-700 font-medium">
              <CheckCircle2 className="h-4 w-4" />
              {savedMsg}
            </span>
          ) : (
            <span className="text-neutral-400">
              Changes take effect immediately without restarting FastAPI.
            </span>
          )}
          <button
            type="submit"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md bg-neutral-900 text-white font-medium hover:bg-neutral-800"
          >
            <Save className="h-3.5 w-3.5" />
            Apply Gemma 4 Configuration
          </button>
        </div>
      </form>
    </div>
  );
}