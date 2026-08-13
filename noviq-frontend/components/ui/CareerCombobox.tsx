import { Input, Label } from "@/components/ui/Input";
import { CAREERS } from "@/lib/careers";

/** A free-text input with a native browser typeahead suggesting from the
 * CAREERS list — never enforces the list, just suggests. */
export function CareerCombobox({
  id,
  label,
  value,
  onChange,
  placeholder = "e.g. Computer Science",
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}) {
  const listId = `${id}-options`;
  return (
    <div>
      <Label htmlFor={id}>{label}</Label>
      <Input
        id={id}
        list={listId}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        autoComplete="off"
      />
      <datalist id={listId}>
        {CAREERS.map((career) => (
          <option key={career} value={career} />
        ))}
      </datalist>
    </div>
  );
}
