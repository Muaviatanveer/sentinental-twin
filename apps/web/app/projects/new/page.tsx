"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { createSampleProject, uploadProject } from "@/lib/api";
import { UploadCloud, Folder, ArrowRight, Loader2, FileCode } from "lucide-react";

export default function NewProjectPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [loading, setLoading] = useState(false);
  const [projectName, setProjectName] = useState("Custom Compose App");
  const [yamlText, setYamlText] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleLoadSample = async () => {
    setLoading(true);
    setError(null);
    try {
      const proj = await createSampleProject();
      router.push(`/projects/${proj.id}/topology`);
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const content = await file.text();
    setYamlText(content);
    setProjectName(file.name.replace(/\.(ya?ml)$/i, "") || "Uploaded Project");
  };

  const handleCustomUpload = async () => {
    if (!yamlText.trim()) {
      setError("Please select or paste a valid Docker Compose YAML file first.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const proj = await uploadProject(projectName, yamlText);
      router.push(`/projects/${proj.id}/topology`);
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-8 space-y-8">
      <div>
        <h1 className="text-xl font-semibold text-neutral-900">
          Import Infrastructure Configuration
        </h1>
        <p className="text-sm text-neutral-500 mt-1">
          Upload any Docker Compose YAML file or load the 3-tier sample commerce fixture to construct an isolated digital twin.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-50 text-red-700 text-xs border border-red-200 rounded-md">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Sample Project Card */}
        <div className="border border-neutral-200 bg-white rounded-lg p-6 flex flex-col items-start hover:border-blue-300 transition-colors">
          <div className="h-10 w-10 bg-blue-50 text-blue-600 rounded-md flex items-center justify-center mb-4">
            <Folder className="h-5 w-5" />
          </div>
          <h3 className="text-sm font-semibold text-neutral-900">
            Open 3-Service Sample Project
          </h3>
          <p className="text-xs text-neutral-500 mt-1 mb-6 leading-relaxed">
            Loads the permissive 3-service Commerce fixture (<code>frontend</code>, <code>api</code>, <code>database</code>) with real BusyBox HTTP/TCP listeners ready for live Docker verification.
          </p>
          <button
            onClick={handleLoadSample}
            disabled={loading}
            className="mt-auto inline-flex items-center gap-2 px-4 py-2 bg-neutral-900 text-white text-xs font-medium rounded-md hover:bg-neutral-800 disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              "Load Sample Fixture"
            )}
            {!loading && <ArrowRight className="h-3.5 w-3.5" />}
          </button>
        </div>

        {/* Real Upload & Paste Card */}
        <div className="border border-neutral-200 bg-white rounded-lg p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <UploadCloud className="h-5 w-5 text-neutral-700" />
              <h3 className="text-sm font-semibold text-neutral-900">
                Upload Custom compose.yaml
              </h3>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".yaml,.yml"
              onChange={handleFileChange}
              className="hidden"
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="px-3 py-1.5 bg-neutral-100 hover:bg-neutral-200 text-neutral-800 text-xs font-medium rounded-md border border-neutral-300"
            >
              Choose File
            </button>
          </div>

          <input
            type="text"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            placeholder="Project Name"
            className="w-full px-3 py-1.5 text-xs border border-neutral-300 rounded-md"
          />

          <textarea
            rows={6}
            value={yamlText}
            onChange={(e) => setYamlText(e.target.value)}
            placeholder="Paste docker-compose.yml content here or click 'Choose File' above..."
            className="w-full p-3 font-mono text-xs border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />

          <button
            onClick={handleCustomUpload}
            disabled={loading}
            className="w-full inline-flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white text-xs font-medium rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            <FileCode className="h-3.5 w-3.5" />
            Parse & Build Infrastructure Twin
          </button>
        </div>
      </div>
    </div>
  );
}