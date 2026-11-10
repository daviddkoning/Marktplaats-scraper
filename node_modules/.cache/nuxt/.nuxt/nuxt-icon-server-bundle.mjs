function createRemoteCollection(fetchEndpoint) {
  let _cache
  return async () => {
    if (_cache)
      return _cache
    _cache = fetch(fetchEndpoint).then(r => r.json()).then((data) => {
      _cache = data
      return data
    }).catch((error) => {
      _cache = undefined
      throw error
    })
    return _cache
  }
}

export const collections = {
  'lucide': () => import('@iconify-json/lucide/icons.json', { with: { type: 'json' } }).then(m => m.default),
  'simple-icons': () => import('@iconify-json/simple-icons/icons.json', { with: { type: 'json' } }).then(m => m.default),
}