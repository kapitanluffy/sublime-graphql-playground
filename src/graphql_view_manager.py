VIEW_REGISTRY = {}

class GraphqlViewManager:
    @staticmethod
    def all():
        return VIEW_REGISTRY

    @staticmethod
    def add(view, resp):
        VIEW_REGISTRY[view] = resp

    @staticmethod
    def get(view):
        return VIEW_REGISTRY.get(view)

    @staticmethod
    def remove(view):
        VIEW_REGISTRY.pop(view)

    @staticmethod
    def removeView(view):
        removables = list(
            filter(
                lambda v: v[1] == view, VIEW_REGISTRY.items()
            )
        )

        for r in removables:
            VIEW_REGISTRY.pop(r[0])

    @staticmethod
    def has(resp):
        return next((v for v in VIEW_REGISTRY if VIEW_REGISTRY[v] == resp), None)
