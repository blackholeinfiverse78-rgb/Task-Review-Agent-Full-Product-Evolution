from evaluation_engine.repository_analyzer import RepositoryAnalyzer
r = RepositoryAnalyzer()
result = r.analyze('https://github.com/octocat/Hello-World')
print('Error:', result.get('error'))
print('Total files:', result.get('structure', {}).get('total_files'))
print('Language:', result.get('metadata', {}).get('language'))
print('Stars:', result.get('metadata', {}).get('stars'))
print('Architecture layers:', result.get('architecture', {}).get('layer_count'))
