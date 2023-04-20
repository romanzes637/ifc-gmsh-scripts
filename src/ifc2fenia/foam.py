def is_float(s):
  try:
    float(s)
    return True
  except ValueError:
    return False


def read(f):
  is_comment = False
  for line in f:
    line = line.strip()
    if line.startswith('/*'):
      is_comment = True
    if line.endswith('*/'):
      is_comment = False
      continue
    if line.startswith('//') or line == '':
      continue
    if not is_comment:
      line = line.split('//')[0].strip()  # remove inline comments
      yield line


def load(f, cls='dictionary', start_from=12):
  for _ in range(start_from):
    next(f)
  if cls == 'dictionary':
    d = {}
    name, kvs = load_object(f)
    while name is not None or len(kvs) > 0:
      d[name] = kvs
      name, kvs = load_object(f)
  elif cls == 'scalarList':
    d = []
    for line in read(f):
      ts = line[:-1].split('(')  # tokens
      _, vs = int(ts[0]), [float(x) for x in ts[1].split()]
      d.append(vs)
    d = d[1:] if len(d) > 1 else d  # slice length
  elif cls == 'wordList':
    d = []
    for line in read(f):
      if line not in ['(', ')'] and not is_float(line):
        d.append(line)
  elif cls == 'wordListList':
    d = []
    for line in read(f):
      if line not in ['(', ')'] and not is_float(line):
        line = line.replace('(', ' ').replace(')', ' ')
        d.append(line.split()[1:])
  elif cls in ['scalarField', 'vectorList', 'vectorField']:
    d = []
    for line in read(f):
      if 'nonuniform' in line or not 'uniform' in line:
        line = line.replace('(', ' ').replace(')', ' ')
        for t in line.split():
          if is_float(t):
            d.append(float(t))
      else:
        d.append(1)
        d.append(float(line.split()[2][:-1]))
    d = d[1:]  # slice length
    if cls in ['vectorList', 'vectorField']:  # TODO numpy reshape?
      d = [d[x:x + 3] for x in range(0, len(d), 3)]
  else:
    raise NotImplementedError(cls)
  return d


def load_object(f, name=None):
  kvs = {}  # key-values
  for line in read(f):
    line = line.replace(';', '')  # remove ending ;
    ts = line.split()  # tokens
    k, vs = ts[0], ts[1:]
    if len(vs) == 0:
      if k == '{':
        continue
      elif k == '}':
        break
      elif name is None and len(kvs) == 0:
        name = k
      else:
        sub_name, sub_kvs = load_object(f, k)
        kvs[sub_name] = sub_kvs
    else:
      if len(vs) > 1:
        if vs[0].startswith('('):
          v = ' '.join(vs)
        else:
          k = ' '.join([k] + vs[:-1])
          v = vs[-1]
      else:
        v = vs[0]
      if v in ['off', 'false']:
        kvs[k] = False
      elif v in ['on', 'true']:
        kvs[k] = True
      elif v.isnumeric():
        kvs[k] = int(v)
      elif is_float(v):
        kvs[k] = float(v)
      else:  # string
        kvs[k] = v
  return name, kvs


def dump(d, f, cls='dictionary'):
  if cls == 'dictionary':
    for name, kvs in d.items():
      dump_object(name, kvs, f)
  else:
    raise NotImplementedError(cls)


def dump_object(name, kvs, f):
  if name is not None:
    f.write(f'{name}\n')
    f.write('{\n')
  for k, v in kvs.items():
    if isinstance(v, list):
      f.write(f'{k} ({" ".join([str(x) for x in v])});\n')
    elif isinstance(v, dict):
      dump_object(k, v, f)
    else:
      f.write(f'{k} {v};\n')
  if name is not None:
    f.write('}\n')
