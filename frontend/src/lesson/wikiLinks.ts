interface MarkdownNode {
  type: string;
  value?: string;
  children?: MarkdownNode[];
  data?: { hName: string; hProperties: Record<string, string> };
}

const WIKI_LINK = /\[\[([^\]\n|]+)(?:\|([^\]\n]+))?\]\]/g;
const SLUG = /^[a-z0-9]+(-[a-z0-9]+)*$/;

function conceptLink(slug: string, label?: string): MarkdownNode {
  return {
    type: "conceptLink",
    data: { hName: "concept-link", hProperties: label ? { slug, label } : { slug } },
    children: [],
  };
}

function splitText(value: string): MarkdownNode[] {
  const nodes: MarkdownNode[] = [];
  let last = 0;
  for (const match of value.matchAll(WIKI_LINK)) {
    const [whole, slug, label] = match;
    if (!SLUG.test(slug!)) continue;
    if (match.index > last) nodes.push({ type: "text", value: value.slice(last, match.index) });
    nodes.push(conceptLink(slug!, label));
    last = match.index + whole.length;
  }
  if (last < value.length) nodes.push({ type: "text", value: value.slice(last) });
  return nodes;
}

function walk(node: MarkdownNode) {
  if (!node.children || node.type === "link") return;
  node.children = node.children.flatMap((child) => {
    if (child.type === "text") return splitText(child.value ?? "");
    walk(child);
    return [child];
  });
}

/** Turns [[slug]] and [[slug|label]] into concept links. Only text nodes are read, so code is safe. */
export function remarkWikiLinks() {
  return walk;
}
