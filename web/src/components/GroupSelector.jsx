import { useGroups } from '../context/GroupContext.jsx';

// Group picker shown in the top bar; selection persists across screens.
export function GroupSelector() {
  const { groups, selectedGroupId, selectGroup } = useGroups();

  if (groups.length === 0) {
    return <span className="hint">Chưa có group nào</span>;
  }
  return (
    <div className="group-selector">
      <select
        value={selectedGroupId}
        onChange={(e) => selectGroup(e.target.value)}
        aria-label="Chọn group"
      >
        {groups.map((g) => (
          <option key={g.id} value={g.id}>
            {g.name}
          </option>
        ))}
      </select>
    </div>
  );
}
