import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';

class ResultScreen extends StatelessWidget {
  final String imagePath;
  final Map<String, dynamic> data;

  const ResultScreen({super.key, required this.imagePath, required this.data});

  @override
  Widget build(BuildContext context) {
    final rawText = data['raw_text'] ?? 'No text extracted';
    final structuredData = data['structured_data'] ?? {};
    final violations = data['violations'] ?? [];
    // If 'compliance_status' is not directly in root, check if it's inferred from violations
    final isCompliant = (data['compliance_status'] == 'COMPLIANT') || (violations.isEmpty);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Inspection Result'),
        backgroundColor: isCompliant ? Colors.green : Colors.orange,
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              height: 250,
              decoration: BoxDecoration(
                image: DecorationImage(
                  image: FileImage(File(imagePath)),
                  fit: BoxFit.cover,
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildStatusCard(isCompliant, violations),
                  const SizedBox(height: 16),
                  _buildSectionTitle('Structured Data'),
                  _buildStructuredData(structuredData),
                  const SizedBox(height: 16),
                  _buildSectionTitle('Extracted Text'),
                  Card(
                     child: Padding(
                       padding: const EdgeInsets.all(12.0),
                       child: Text(rawText, style: const TextStyle(fontSize: 13, fontFamily: 'monospace')),
                     ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusCard(bool isCompliant, List violations) {
    return Card(
      color: isCompliant ? Colors.green.shade50 : Colors.red.shade50,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Icon(
              isCompliant ? Icons.check_circle : Icons.warning,
              size: 48,
              color: isCompliant ? Colors.green : Colors.red,
            ),
            const SizedBox(height: 8),
            Text(
              isCompliant ? 'COMPLIANT' : 'NON-COMPLIANT',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: isCompliant ? Colors.green.shade800 : Colors.red.shade800,
              ),
            ),
             if (!isCompliant) ...[
              const SizedBox(height: 12),
              const Divider(),
              ...violations.map((v) => ListTile(
                leading: const Icon(Icons.error_outline, color: Colors.red),
                title: Text(v.toString(), style: const TextStyle(fontSize: 13)),
              )),
            ]
          ],
        ),
      ),
    );
  }
  
  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0),
      child: Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
    );
  }

  Widget _buildStructuredData(Map data) {
    if (data.isEmpty) return const Text('No structured data found.');
    return Card(
      child: Column(
        children: data.entries.map((e) => ListTile(
          title: Text(e.key.toString().toUpperCase(), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
          subtitle: Text(e.value.toString(), style: const TextStyle(fontSize: 14)),
        )).toList(),
      ),
    );
  }
}
