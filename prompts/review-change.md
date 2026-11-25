# Review prompt

Review the exact PR head against its base. Trace each changed public behavior to a requirement and executed assertion. Check signed/expired JWTs, owner-qualified URL/body references, atomic writes, whole-batch recipe validation, declared exclusions, error sanitization, schema upgrades and old-data preservation. Check keyboard use, labelled validation and all empty/error/loading screens when UI changes.

Classify concrete findings by severity, affected file/line, trigger and impact. Separate observed failures from unverified risks. Confirm source revisions in coverage/load/Sonar evidence. Do not claim live-provider or cloud success from mocks or a Docker build. Keep human approval and tool output distinct.
