{{- define "pic2cookie.fullname" -}}
{{- if contains .Chart.Name .Release.Name }}{{ .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}{{ printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" }}{{ end }}
{{- end }}

{{- define "pic2cookie.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end }}

{{- define "pic2cookie.selector" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "pic2cookie.image" -}}
{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}
{{- end }}

{{/* The worker shares the app pod when files are on a (usually RWO) volume. */}}
{{- define "pic2cookie.sidecarWorker" -}}
{{- if and (eq .Values.executor "rq") (eq .Values.storage.type "fs") }}true{{ end }}
{{- end }}

{{- define "pic2cookie.secretName" -}}
{{ include "pic2cookie.fullname" . }}
{{- end }}

{{- define "pic2cookie.env" -}}
- name: PIC2COOKIE_STORAGE__TYPE
  value: {{ .Values.storage.type | quote }}
- name: PIC2COOKIE_STORAGE__PATH
  value: /data
{{- if eq .Values.storage.type "s3" }}
- name: PIC2COOKIE_STORAGE__BUCKET
  value: {{ required "storage.s3.bucket is required" .Values.storage.s3.bucket | quote }}
- name: PIC2COOKIE_STORAGE__PREFIX
  value: {{ .Values.storage.s3.prefix | quote }}
{{- with .Values.storage.s3.endpointUrl }}
- name: PIC2COOKIE_STORAGE__ENDPOINT_URL
  value: {{ . | quote }}
{{- end }}
{{- with .Values.storage.s3.region }}
- name: PIC2COOKIE_STORAGE__REGION
  value: {{ . | quote }}
{{- end }}
{{- if or .Values.storage.s3.existingSecret .Values.storage.s3.accessKeyId }}
- name: PIC2COOKIE_STORAGE__ACCESS_KEY_ID
  valueFrom:
    secretKeyRef:
      name: {{ .Values.storage.s3.existingSecret | default (include "pic2cookie.secretName" .) }}
      key: access-key-id
- name: PIC2COOKIE_STORAGE__SECRET_ACCESS_KEY
  valueFrom:
    secretKeyRef:
      name: {{ .Values.storage.s3.existingSecret | default (include "pic2cookie.secretName" .) }}
      key: secret-access-key
{{- end }}
{{- end }}
{{- if .Values.mongodb.enabled }}
- name: PIC2COOKIE_DATABASE__URI
  value: {{ printf "mongodb://%s-mongodb:27017" (include "pic2cookie.fullname" .) | quote }}
{{- else if .Values.database.existingSecret }}
- name: PIC2COOKIE_DATABASE__URI
  valueFrom:
    secretKeyRef:
      name: {{ .Values.database.existingSecret }}
      key: uri
{{- else if .Values.database.uri }}
- name: PIC2COOKIE_DATABASE__URI
  valueFrom:
    secretKeyRef:
      name: {{ include "pic2cookie.secretName" . }}
      key: database-uri
{{- end }}
- name: PIC2COOKIE_DATABASE__NAME
  value: {{ .Values.database.name | quote }}
- name: PIC2COOKIE_EXECUTOR
  value: {{ .Values.executor | quote }}
{{- if eq .Values.executor "rq" }}
- name: PIC2COOKIE_REDIS_URL
  value: {{ .Values.redis.url | default (printf "redis://%s-redis:6379/0" (include "pic2cookie.fullname" .)) | quote }}
{{- end }}
{{- with .Values.retention.days }}
- name: PIC2COOKIE_RETENTION__DAYS
  value: {{ . | quote }}
{{- end }}
- name: PIC2COOKIE_LIMITS__UPLOAD_MB
  value: {{ .Values.limits.uploadMb | quote }}
- name: PIC2COOKIE_LIMITS__MAX_PIXELS
  value: {{ .Values.limits.maxPixels | quote }}
- name: PIC2COOKIE_LIMITS__JOB_TIMEOUT
  value: {{ .Values.limits.jobTimeout | quote }}
{{- with .Values.extraEnv }}
{{ toYaml . }}
{{- end }}
{{- end }}
