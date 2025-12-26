import { useState, useEffect, useCallback } from 'react';
import { Wand2, RefreshCw, ChevronRight, FileText, Loader2, FolderOpen } from 'lucide-react';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { cn } from '../lib/utils';
import { useProjectStore } from '../stores/project-store';

interface Skill {
    id: string;
    name: string;
    description: string;
    allowedTools: string[];
    path: string;
}

interface SkillsProps {
    projectId: string;
}

// Parse YAML frontmatter from SKILL.md content using regex
function parseSkillFrontmatter(content: string): { name?: string; description?: string; allowedTools?: string[] } {
    const match = content.match(/^---\s*\n([\s\S]*?)\n---/);
    if (!match) return {};

    const frontmatter = match[1];
    const result: { name?: string; description?: string; allowedTools?: string[] } = {};

    // Parse name
    const nameMatch = frontmatter.match(/^name:\s*(.+)$/m);
    if (nameMatch) {
        result.name = nameMatch[1].trim().replace(/^["']|["']$/g, '');
    }

    // Parse description
    const descMatch = frontmatter.match(/^description:\s*(.+)$/m);
    if (descMatch) {
        result.description = descMatch[1].trim().replace(/^["']|["']$/g, '');
    }

    // Parse allowed-tools (inline array format)
    const toolsMatch = frontmatter.match(/^allowed-tools:\s*\[([^\]]+)\]/m);
    if (toolsMatch) {
        result.allowedTools = toolsMatch[1]
            .split(',')
            .map(t => t.trim().replace(/^["']|["']$/g, ''))
            .filter(t => t);
    }

    return result;
}

export function Skills({ projectId }: SkillsProps) {
    const [skills, setSkills] = useState<Skill[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null);
    const [skillContent, setSkillContent] = useState<string | null>(null);
    const [loadingContent, setLoadingContent] = useState(false);

    const project = useProjectStore((state) => state.projects.find(p => p.id === projectId));

    const loadSkills = useCallback(async () => {
        if (!project?.path) {
            setError('Project path not found');
            setLoading(false);
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const skillsDir = `${project.path}/.claude/skills`;
            const result = await window.electronAPI.listDirectory(skillsDir);

            if (!result.success) {
                // Directory doesn't exist or can't be read
                setSkills([]);
                setLoading(false);
                return;
            }

            const discoveredSkills: Skill[] = [];

            // Filter directories that don't start with underscore
            const skillFolders = (result.data || []).filter(
                node => node.isDirectory && !node.name.startsWith('_')
            );

            // For each skill folder, try to read SKILL.md
            for (const folder of skillFolders) {
                const skillMdPath = `${skillsDir}/${folder.name}/SKILL.md`;
                try {
                    // We don't have a direct file read API, so we'll just add the skill with folder name
                    // The full content will be loaded when user clicks on a skill
                    discoveredSkills.push({
                        id: folder.name,
                        name: folder.name,
                        description: 'Click to load skill details',
                        allowedTools: [],
                        path: `${skillsDir}/${folder.name}`
                    });
                } catch {
                    // Skip skills that can't be parsed
                }
            }

            setSkills(discoveredSkills);
        } catch (err) {
            console.error('Failed to load skills:', err);
            setError(err instanceof Error ? err.message : 'Failed to load skills');
        } finally {
            setLoading(false);
        }
    }, [project?.path]);

    useEffect(() => {
        loadSkills();
    }, [loadSkills]);

    const handleSkillClick = (skill: Skill) => {
        setSelectedSkill(selectedSkill?.id === skill.id ? null : skill);
        setSkillContent(null); // Clear previous content
    };

    const openSkillFolder = async (skillPath: string) => {
        try {
            await window.electronAPI.openExternal(`file://${skillPath}`);
        } catch (err) {
            console.error('Failed to open skill folder:', err);
        }
    };

    return (
        <div className="flex h-full flex-col">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-border px-6 py-4">
                <div className="flex items-center gap-2">
                    <Wand2 className="h-5 w-5 text-primary" />
                    <h2 className="text-lg font-semibold text-foreground">Skills</h2>
                    <span className="text-sm text-muted-foreground">({skills.length})</span>
                </div>
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={loadSkills}
                    disabled={loading}
                >
                    <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
                </Button>
            </div>

            {/* Content */}
            <div className="flex flex-1 overflow-hidden">
                {/* Skills list */}
                <ScrollArea className="w-80 border-r border-border">
                    <div className="p-4 space-y-2">
                        {loading ? (
                            <div className="flex items-center justify-center py-8">
                                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                            </div>
                        ) : error ? (
                            <div className="text-center py-8">
                                <p className="text-sm text-destructive">{error}</p>
                                <Button variant="outline" size="sm" className="mt-4" onClick={loadSkills}>
                                    Retry
                                </Button>
                            </div>
                        ) : skills.length === 0 ? (
                            <div className="text-center py-8">
                                <Wand2 className="h-12 w-12 mx-auto text-muted-foreground/50" />
                                <h3 className="mt-4 text-lg font-semibold text-foreground">No Skills Found</h3>
                                <p className="mt-2 text-sm text-muted-foreground">
                                    Add skills to <code className="text-xs bg-muted px-1 py-0.5 rounded">.claude/skills/</code>
                                </p>
                            </div>
                        ) : (
                            skills.map((skill) => (
                                <button
                                    key={skill.id}
                                    onClick={() => handleSkillClick(skill)}
                                    className={cn(
                                        "w-full text-left rounded-lg border p-3 transition-colors",
                                        "hover:bg-accent hover:border-accent-foreground/20",
                                        selectedSkill?.id === skill.id
                                            ? "bg-accent border-primary"
                                            : "border-border bg-card"
                                    )}
                                >
                                    <div className="flex items-center justify-between">
                                        <span className="font-medium text-foreground">{skill.name}</span>
                                        <ChevronRight className={cn(
                                            "h-4 w-4 text-muted-foreground transition-transform",
                                            selectedSkill?.id === skill.id && "rotate-90"
                                        )} />
                                    </div>
                                    <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
                                        {skill.description}
                                    </p>
                                </button>
                            ))
                        )}
                    </div>
                </ScrollArea>

                {/* Skill detail panel */}
                <div className="flex-1 overflow-hidden">
                    {selectedSkill ? (
                        <ScrollArea className="h-full">
                            <div className="p-6">
                                <div className="flex items-center justify-between mb-4">
                                    <div className="flex items-center gap-2">
                                        <FileText className="h-5 w-5 text-primary" />
                                        <h3 className="text-lg font-semibold text-foreground">{selectedSkill.name}</h3>
                                    </div>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => openSkillFolder(selectedSkill.path)}
                                    >
                                        <FolderOpen className="h-4 w-4 mr-2" />
                                        Open Folder
                                    </Button>
                                </div>

                                <div className="rounded-lg bg-muted p-4 mb-4">
                                    <p className="text-sm text-muted-foreground">
                                        <strong>Path:</strong> <code className="text-xs bg-background px-1 py-0.5 rounded">{selectedSkill.path}</code>
                                    </p>
                                </div>

                                <div className="rounded-lg bg-muted/50 p-4 border border-dashed border-border">
                                    <p className="text-sm text-muted-foreground text-center">
                                        Skills are loaded into autonomous agents at runtime.
                                        <br />
                                        Use "Open Folder" to view and edit the SKILL.md file.
                                    </p>
                                </div>
                            </div>
                        </ScrollArea>
                    ) : (
                        <div className="flex h-full items-center justify-center">
                            <div className="text-center">
                                <Wand2 className="h-12 w-12 mx-auto text-muted-foreground/30" />
                                <p className="mt-4 text-sm text-muted-foreground">
                                    Select a skill to view details
                                </p>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
