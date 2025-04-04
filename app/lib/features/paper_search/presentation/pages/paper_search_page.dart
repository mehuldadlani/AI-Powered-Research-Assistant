import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/paper_providers.dart';
import '../widgets/paper_list_item.dart';

class PaperSearchPage extends ConsumerWidget {
  const PaperSearchPage({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final papersAsyncValue = ref.watch(papersProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Paper Search')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: TextField(
              decoration: const InputDecoration(
                hintText: 'Search papers...',
                border: OutlineInputBorder(),
              ),
              onSubmitted: (query) {
                ref.read(papersProvider.notifier).searchPapers(query);
              },
            ),
          ),
          Expanded(
            child: papersAsyncValue.when(
              data: (papers) => ListView.builder(
                itemCount: papers.length,
                itemBuilder: (context, index) => PaperListItem(paper: papers[index]),
              ),
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (error, stackTrace) => Center(child: Text('Error: $error')),
            ),
          ),
        ],
      ),
    );
  }
}