import { useEffect, useRef, useCallback } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { FileTreeItem } from './FileTreeItem';
import { useFileExplorerStore } from '../stores/file-explorer-store';
import { useVirtualizedTree } from '../hooks/useVirtualizedTree';
import { Loader2, AlertCircle, FolderOpen } from 'lucide-react';

interface FileTreeProps {
  rootPath: string;
}

// Estimated height of each tree item in pixels
const ITEM_HEIGHT = 28;
// Number of items to render outside the visible area for smoother scrolling
const OVERSCAN = 10;

export function FileTree({ rootPath }: FileTreeProps) {
  // This ref is the scroll container - FileTree manages its own scrolling
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  const {
    loadDirectory,
    isLoadingDir,
    error
  } = useFileExplorerStore();

  const {
    flattenedNodes,
    count,
    handleToggle,
    isRootLoading,
    hasRootFiles
  } = useVirtualizedTree(rootPath);

  const loading = isLoadingDir(rootPath);

  // Load root directory on mount
  useEffect(() => {
    if (!hasRootFiles && !loading) {
      loadDirectory(rootPath);
    }
  }, [rootPath, hasRootFiles, loading, loadDirectory]);

  // Set up the virtualizer with the internal scroll container
  const rowVirtualizer = useVirtualizer({
    count,
    getScrollElement: () => scrollContainerRef.current,
    estimateSize: () => ITEM_HEIGHT,
    overscan: OVERSCAN,
  });

  // Create toggle handler for each item
  const createToggleHandler = useCallback(
    (index: number) => {
      return () => {
        const item = flattenedNodes[index];
        if (item) {
          handleToggle(item.node);
        }
      };
    },
    [flattenedNodes, handleToggle]
  );

  if (isRootLoading && !hasRootFiles) {
    return (
      <div className="flex items-center justify-center py-8 h-full">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-8 px-4 text-center h-full">
        <AlertCircle className="h-5 w-5 text-destructive mb-2" />
        <p className="text-xs text-destructive">{error}</p>
      </div>
    );
  }

  if (!hasRootFiles || count === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 px-4 text-center h-full">
        <FolderOpen className="h-6 w-6 text-muted-foreground mb-2" />
        <p className="text-xs text-muted-foreground">No files found</p>
      </div>
    );
  }

  // FileTree is now self-contained with its own scroll container
  return (
    <div
      ref={scrollContainerRef}
      className="h-full w-full overflow-auto force-scrollbar"
      style={{ overscrollBehavior: 'contain' }}
    >
      {/* Inner content div with calculated height for proper scrolling */}
      <div
        style={{
          height: `${rowVirtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
          padding: '4px'
        }}
      >
        {/* Only the visible items in the virtualizer */}
        {rowVirtualizer.getVirtualItems().map((virtualItem) => {
          const item = flattenedNodes[virtualItem.index];
          if (!item) return null;

          return (
            <div
              key={item.key}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualItem.size}px`,
                transform: `translateY(${virtualItem.start}px)`,
              }}
            >
              <FileTreeItem
                node={item.node}
                depth={item.depth}
                isExpanded={item.isExpanded}
                isLoading={item.isLoading}
                onToggle={createToggleHandler(virtualItem.index)}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}
