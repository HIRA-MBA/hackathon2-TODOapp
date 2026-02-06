{{/*
Expand the name of the chart.
*/}}
{{- define "todo-chatbot.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "todo-chatbot.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "todo-chatbot.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "todo-chatbot.labels" -}}
helm.sh/chart: {{ include "todo-chatbot.chart" . }}
{{ include "todo-chatbot.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "todo-chatbot.selectorLabels" -}}
app.kubernetes.io/name: {{ include "todo-chatbot.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Frontend labels
*/}}
{{- define "todo-chatbot.frontend.labels" -}}
{{ include "todo-chatbot.labels" . }}
app.kubernetes.io/component: frontend
{{- end }}

{{/*
Frontend selector labels
*/}}
{{- define "todo-chatbot.frontend.selectorLabels" -}}
{{ include "todo-chatbot.selectorLabels" . }}
app.kubernetes.io/component: frontend
{{- end }}

{{/*
Backend labels
*/}}
{{- define "todo-chatbot.backend.labels" -}}
{{ include "todo-chatbot.labels" . }}
app.kubernetes.io/component: backend
{{- end }}

{{/*
Backend selector labels
*/}}
{{- define "todo-chatbot.backend.selectorLabels" -}}
{{ include "todo-chatbot.selectorLabels" . }}
app.kubernetes.io/component: backend
{{- end }}

{{/*
ConfigMap name
*/}}
{{- define "todo-chatbot.configmapName" -}}
{{ include "todo-chatbot.fullname" . }}-config
{{- end }}

{{/*
Secret name
*/}}
{{- define "todo-chatbot.secretName" -}}
{{ include "todo-chatbot.fullname" . }}-secrets
{{- end }}

{{/*
WebSocket service labels
*/}}
{{- define "todo-chatbot.websocket.labels" -}}
{{ include "todo-chatbot.labels" . }}
app.kubernetes.io/component: websocket
{{- end }}

{{/*
WebSocket service selector labels
*/}}
{{- define "todo-chatbot.websocket.selectorLabels" -}}
{{ include "todo-chatbot.selectorLabels" . }}
app.kubernetes.io/component: websocket
{{- end }}

{{/*
Recurring task service labels
*/}}
{{- define "todo-chatbot.recurring.labels" -}}
{{ include "todo-chatbot.labels" . }}
app.kubernetes.io/component: recurring-task
{{- end }}

{{/*
Recurring task service selector labels
*/}}
{{- define "todo-chatbot.recurring.selectorLabels" -}}
{{ include "todo-chatbot.selectorLabels" . }}
app.kubernetes.io/component: recurring-task
{{- end }}

{{/*
Notification service labels
*/}}
{{- define "todo-chatbot.notification.labels" -}}
{{ include "todo-chatbot.labels" . }}
app.kubernetes.io/component: notification
{{- end }}

{{/*
Notification service selector labels
*/}}
{{- define "todo-chatbot.notification.selectorLabels" -}}
{{ include "todo-chatbot.selectorLabels" . }}
app.kubernetes.io/component: notification
{{- end }}

{{/*
Dapr annotations for sidecar injection
*/}}
{{- define "todo-chatbot.dapr.annotations" -}}
dapr.io/enabled: "true"
dapr.io/app-port: "{{ .port }}"
dapr.io/app-id: "{{ .appId }}"
dapr.io/app-protocol: "http"
dapr.io/enable-metrics: "true"
dapr.io/metrics-port: "9090"
{{- end }}
