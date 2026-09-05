"""OBDS 4.0: reproduce all governed slots from a compiled universe.

Only element identities and fixed renderer metadata are accepted as projection
instructions. External chapter prose is never used as governed model content.
"""
from __future__ import annotations
import json
try:
    from .canonical import identity_key
except ImportError:
    from canonical import identity_key

def _compact_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def render_element(element):
    value = element.get("value")
    if isinstance(value, str):
        rendered = value
    elif value is None:
        rendered = ""
    else:
        rendered = _compact_json(value)
    return f"{identity_key(element['id'])} [{element['state']}]: {rendered}".rstrip()


def render_rule_for_model(element):
    value = element.get("value") or {}
    prefix = f"{identity_key(element['id'])} [{value.get('obligation','?')}/{value.get('enforcement','inform')}]"
    parts = [f"{prefix}: {value.get('statement','').strip()}"]
    refs = value.get("references") or []
    if refs:
        # Section 8.0a: a reference names an identity, so the model sees the
        # canonical form. Rendering the stored spelling made two canonically
        # equivalent rules render differently while text_hash, which normalises,
        # reported the same modelInputHash for both.
        parts.append("refs=" + ",".join(identity_key(item) for item in refs))
    condition = value.get("condition") or {}
    if condition:
        parts.append("condition=" + _compact_json(condition))
    requirement = value.get("requirement") or {}
    if requirement:
        parts.append("requirement=" + _compact_json(requirement))
    checks = value.get("checks") or []
    if checks:
        compact_checks = []
        for check in checks:
            primitive = check.get("primitive", "check")
            params = dict(check.get("params") or {})
            reference = params.get("elementValueRef")
            if isinstance(reference, dict) and isinstance(reference.get("elementId"), str):
                reference = dict(reference)
                reference["elementId"] = identity_key(reference["elementId"])
                params["elementValueRef"] = reference
            compact_checks.append(primitive + "(" + _compact_json(params) + ")")
        parts.append("checks=" + ";".join(compact_checks))
    return " | ".join(parts)



def chapter_content(records, element_ids):
    blocks = []
    for raw in element_ids:
        key = identity_key(raw)
        if key not in records:
            raise ValueError('Reasoning Chapter declares elements outside compiled universe: ' + key)
        item = records[key]
        value = item.get('value')
        rendered = value if isinstance(value, str) else _compact_json(value)
        if 'value' not in item:
            rendered = 'No value.'
        blocks.append(f"## {key} [{item.get('family')}/{item.get('kind')}/{item.get('state')}]\n{rendered}")
    return '\n\n'.join(blocks)


def derive_projection(context, selection, projection, *, delivery_mode, application_mode):
    """Return slots and canonical selection. No received slot text is consulted."""
    if projection.get('renderer') != 'obds:compiled-projection-v1':
        raise ValueError('unsupported governed projection renderer')
    records = {identity_key(e['id']): e for e in context['elementRecords']}
    if len(records) != len(context['elementRecords']):
        raise ValueError('duplicate element IDs in compiled universe')
    if set(records) != {identity_key(x) for x in context['availableElementIds']}:
        raise ValueError('compiled universe mismatch')
    included = {identity_key(x) for x in context['includedElementIds']}
    if not included.issubset(records):
        raise ValueError('compiled included elements outside universe')
    policy = context.get('contextAssembly')
    if not isinstance(policy, dict) or delivery_mode != policy.get('deliveryMode') or application_mode != policy.get('applicationMode'):
        raise ValueError('projection modes do not match compiled policy')

    def selected(key):
        raw = selection[key]
        ids = [identity_key(x) for x in raw]
        if len(ids) != len(set(ids)) or not set(ids).issubset(records):
            raise ValueError('duplicate or unavailable projection element: ' + key)
        return set(ids)

    facts = selected('factElementIds')
    gaps = selected('gapElementIds')
    active = selected('activeGuidanceElementIds')
    eligible = {identity_key(x) for x in policy.get('eligibleGuidanceIds', [])}
    if not active.issubset(eligible):
        raise ValueError('active guidance is not eligible for compiled target')
    if application_mode == 'compliance' and active:
        raise ValueError('compliance mode cannot activate expression guidance')
    hard = {k for k, e in records.items() if e['family'] == 'rules' and e['state'] == 'defined'
            and (e['value'].get('enforcement') in {'block', 'require_approval'} or e['value'].get('obligation') == 'prohibit')}
    for k in facts:
        if records[k]['state'] != 'defined' or records[k]['family'] == 'rules':
            raise ValueError('fact selection does not name a defined non-rule element')
    for k in gaps:
        if records[k]['state'] == 'defined':
            raise ValueError('gap selection names a defined element')
    for k in active:
        if records[k]['state'] != 'defined' or records[k]['family'] == 'rules':
            raise ValueError('active guidance does not name defined non-rule guidance')
    # Compiler-preserved facts/gaps cannot be lost by a smaller retrieval selection.
    facts |= {k for k in included if records[k]['state'] == 'defined' and records[k]['nature'] == 'fact' and records[k]['family'] != 'rules'}
    gaps |= {k for k in included if records[k]['state'] != 'defined'}
    if delivery_mode == 'full':
        facts |= {k for k,e in records.items() if e['state'] == 'defined' and e['nature'] == 'fact' and e['family'] != 'rules'}
        gaps |= {k for k,e in records.items() if e['state'] != 'defined'}

    chapters = projection['chapters']
    chapter_ids = [identity_key(c['id']) for c in chapters]
    requested_chapters = [identity_key(c) for c in selection['reasoningChapterIds']]
    if len(chapter_ids) != len(set(chapter_ids)) or set(chapter_ids) != set(requested_chapters):
        raise ValueError('projection chapter selection mismatch')
    if delivery_mode == 'reasoning' and not chapters:
        raise ValueError('reasoning mode requires at least one chapter')
    background = set()
    for c in chapters:
        ids = [identity_key(x) for x in c['elementIds']]
        if len(ids) != len(set(ids)) or not set(ids).issubset(records):
            raise ValueError('chapter selection outside compiled universe or duplicate')
        background.update(ids)
    # Included knowledge may contain required truth even when it is not active
    # expression guidance. Preserve it as context, never as an expression duty.
    background |= {k for k in included if records[k]['state'] == 'defined' and records[k]['nature'] == 'knowledge'}
    background -= hard | facts | gaps | active
    parts = []
    if active:
        parts.append('[ACTIVE_GUIDANCE]\n' + '\n'.join(render_element(records[k]) for k in sorted(active)))
    if background:
        parts.append('[REASONING_CHAPTERS]\nGenerated relationship context. '
                     'Only elements listed under ACTIVE_GUIDANCE are expression requirements for this task.\n\n'
                     + chapter_content(records, sorted(background)))
    slots = {
        'hardBoundaries': '\n'.join(render_rule_for_model(records[k]) for k in sorted(hard)),
        'factGrounding': '\n'.join(render_element(records[k]) for k in sorted(facts)),
        'stateMap': '\n'.join(render_element(records[k]) for k in sorted(gaps)),
        'guidanceContext': '\n\n'.join(parts),
    }
    resolved = dict(selection, hardBoundaryElementIds=sorted(hard), factElementIds=sorted(facts),
                    gapElementIds=sorted(gaps), activeGuidanceElementIds=sorted(active))
    return slots, resolved


def verify_projection(context, package):
    slots, selection = derive_projection(context, package['selection'], package['projection'],
        delivery_mode=package['deliveryMode'], application_mode=package['applicationMode'])
    for key, value in slots.items():
        if package['slots'][key] != value:
            raise ValueError('governed projection provenance mismatch: ' + key)
    for key in ('hardBoundaryElementIds', 'factElementIds', 'gapElementIds', 'activeGuidanceElementIds'):
        if [identity_key(x) for x in package['selection'][key]] != selection[key]:
            raise ValueError('governed projection selection mismatch: ' + key)
    return True
