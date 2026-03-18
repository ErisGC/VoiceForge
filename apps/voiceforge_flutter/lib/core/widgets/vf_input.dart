import 'package:flutter/material.dart';

class VFInput extends StatelessWidget {
  const VFInput({
    super.key,
    required this.label,
    this.hintText,
    this.obscureText = false,
    this.maxLines = 1,
    this.prefixIcon,
    this.controller,
    this.enabled = true,
    this.readOnly = false,
    this.keyboardType,
    this.onChanged,
  });

  final String label;
  final String? hintText;
  final bool obscureText;
  final int maxLines;
  final IconData? prefixIcon;
  final TextEditingController? controller;
  final bool enabled;
  final bool readOnly;
  final TextInputType? keyboardType;
  final ValueChanged<String>? onChanged;

  static InputDecoration decoration({
    required String label,
    String? hintText,
    IconData? prefixIcon,
  }) {
    return InputDecoration(
      labelText: label,
      hintText: hintText,
      prefixIcon: prefixIcon == null ? null : Icon(prefixIcon),
    );
  }

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      enabled: enabled,
      readOnly: readOnly,
      obscureText: obscureText,
      maxLines: maxLines,
      keyboardType: keyboardType,
      onChanged: onChanged,
      decoration: decoration(
        label: label,
        hintText: hintText,
        prefixIcon: prefixIcon,
      ),
    );
  }
}
