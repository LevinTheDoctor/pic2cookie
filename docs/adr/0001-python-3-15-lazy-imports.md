# Python 3.15 with explicit lazy imports

We require Python 3.15 or newer and use PEP 810 `lazy import` for heavy dependencies (trimesh, shapely, opencv, boto3, redis). This keeps the CLI's startup instant (`pic2cookie --help` never loads geometry or cloud libraries) without scattering imports inside functions. The cost: the code is a syntax error on older Pythons, and lint and type-checking tools may lag behind the new syntax.
