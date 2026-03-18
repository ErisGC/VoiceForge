# VoiceForge Flutter

Frontend multiplataforma de VoiceForge para Android y Web.

## Design system

- Tokens base: `lib/app/design_system/`
- Tema global: `lib/app/app_theme.dart`
- Componentes reutilizables: `lib/core/widgets/`

## Uso

- Usa `AppColors`, `AppSpacing`, `AppRadius`, `AppGradients` y `AppTypography` para evitar hardcodes visuales.
- Envuelve pantallas de producto con `VFPageScaffold` para mantener ancho, padding y ritmo vertical consistentes.
- Prefiere `VFButton`, `VFCard`, `VFPanel`, `VFInput`, `VFChip`, `VFStatusBadge`, `VFSectionHeader` y `VFWaveformContainer` antes de crear variantes ad hoc.

## Extensión

- Añade nuevos tokens en `lib/app/design_system/` cuando el patrón sea global.
- Si una pieza visual se repite en dos o más pantallas, conviértela en componente dentro de `lib/core/widgets/`.
- Mantén el lenguaje de UI orientado a producto: claro, sobrio y sin exponer términos internos del pipeline.
