import 'package:flutter/material.dart';
import '../../domain/entities/paper.dart';

class PaperListItem extends StatelessWidget {
  final Paper paper;

  const PaperListItem({Key? key, required this.paper}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
      child: ListTile(
        title: Text(
          paper.title,
          style: Theme.of(context).textTheme.titleMedium,
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Text(
              'Authors: ${paper.authors.join(", ")}',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 4),
            Text(
              paper.abstract,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ],
        ),
        onTap: () {
          // TODO: Implement paper details view
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Tapped on paper: ${paper.title}')),
          );
        },
      ),
    );
  }
}